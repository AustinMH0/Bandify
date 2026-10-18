import os

import pytest

yaml = pytest.importorskip("yaml")

TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "..", "template-searchresults.yaml")


class CfnLoader(yaml.SafeLoader):
    """Reads CloudFormation short-form tags (!Ref, !GetAtt, ...) as plain dicts."""


def _tag(loader, suffix, node):
    name = "Ref" if suffix == "Ref" else f"Fn::{suffix}"
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
        if suffix == "GetAtt":
            value = value.split(".", 1)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node, deep=True)
    else:
        value = loader.construct_mapping(node, deep=True)
    return {name: value}


CfnLoader.add_multi_constructor("!", _tag)


@pytest.fixture(scope="module")
def resources():
    with open(TEMPLATE) as f:
        return yaml.load(f, Loader=CfnLoader)["Resources"]


def test_function_runs_in_the_private_subnets(resources):
    vpc = resources["SearchResultsFunction"]["Properties"]["VpcConfig"]
    assert vpc["SecurityGroupIds"] == [{"Ref": "SearchResultsSecurityGroup"}]
    assert vpc["SubnetIds"] == [{"Ref": "PrivateSubnetA"}, {"Ref": "PrivateSubnetB"}]
    for name in ("PrivateSubnetA", "PrivateSubnetB"):
        assert resources[name]["Properties"]["MapPublicIpOnLaunch"] is False


def test_private_subnets_span_two_availability_zones(resources):
    zones = [resources[n]["Properties"]["AvailabilityZone"] for n in ("PrivateSubnetA", "PrivateSubnetB")]
    assert zones[0] != zones[1]


def test_private_subnets_reach_the_internet_through_the_nat_gateway(resources):
    route = resources["PrivateDefaultRoute"]["Properties"]
    assert route["DestinationCidrBlock"] == "0.0.0.0/0"
    assert route["NatGatewayId"] == {"Ref": "NatGateway"}
    assert route["RouteTableId"] == {"Ref": "PrivateRouteTable"}

    associated = {
        r["Properties"]["SubnetId"]["Ref"]
        for r in resources.values()
        if r["Type"] == "AWS::EC2::SubnetRouteTableAssociation"
        and r["Properties"]["RouteTableId"] == {"Ref": "PrivateRouteTable"}
    }
    assert associated == {"PrivateSubnetA", "PrivateSubnetB"}

    nat = resources["NatGateway"]["Properties"]
    assert nat["SubnetId"] == {"Ref": "NatPublicSubnetId"}
    assert nat["AllocationId"] == {"Fn::GetAtt": ["NatGatewayIp", "AllocationId"]}


def test_database_admits_only_the_function_security_group(resources):
    ingress = [r["Properties"] for r in resources.values() if r["Type"] == "AWS::EC2::SecurityGroupIngress"]
    assert ingress == [{
        "GroupId": {"Ref": "DatabaseSecurityGroupId"},
        "IpProtocol": "tcp",
        "FromPort": 5432,
        "ToPort": 5432,
        "SourceSecurityGroupId": {"Ref": "SearchResultsSecurityGroup"},
        "Description": "Postgres from the search results Lambda",
    }]
    # Nothing in this stack opens the database to an address range
    assert not any("CidrIp" in rule for rule in ingress)


def test_function_role_can_manage_vpc_network_interfaces(resources):
    role = resources["SearchResultsExecutionRole"]["Properties"]
    # Inline, so deploying needs no iam:AttachRolePolicy
    assert "ManagedPolicyArns" not in role
    statements = role["Policies"][0]["PolicyDocument"]["Statement"]
    actions = {a for s in statements for a in s["Action"]}
    assert {
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:AssignPrivateIpAddresses",
        "ec2:UnassignPrivateIpAddresses",
    } <= actions


def test_function_timeout_stays_under_api_gateway_limit(resources):
    assert resources["SearchResultsFunction"]["Properties"]["Timeout"] < 29


def test_scraper_uses_existing_session_secret_and_workflow_passes_it():
    directory = os.path.dirname(TEMPLATE)
    with open(os.path.join(directory, "template-playwright.yaml")) as source:
        template = yaml.load(source, Loader=CfnLoader)
    secret = template["Parameters"]["SessionSecret"]
    assert secret["NoEcho"] is True and secret["MinLength"] >= 32
    environment = template["Resources"]["PlaywrightFunction"]["Properties"]["Environment"]["Variables"]
    assert environment["SESSION_SECRET"] == {"Ref": "SessionSecret"}
    with open(os.path.join(directory, "..", "..", ".github", "workflows", "sam_deploy.yaml")) as source:
        workflow = yaml.safe_load(source)
    steps = [step for job in workflow["jobs"].values() for step in job["steps"]]
    deploy = next(step for step in steps if step.get("name") == "Deploy Playwright Stack")
    assert deploy["env"]["SESSION_SECRET"] == "${{ secrets.SESSION_SECRET }}"
    assert "SessionSecret=$SESSION_SECRET" in deploy["run"]
