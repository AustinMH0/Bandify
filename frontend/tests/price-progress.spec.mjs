import { test, expect } from '@playwright/test';

const tracks = [
  { name: 'Blinding Lights', artist: 'The Weeknd' },
  { name: 'Deja Vu', artist: 'Beyonce' },
];

async function openPlaylist(page) {
  await page.route('https://prices.test/get_playlists', route => route.fulfill({ json: {
    id: 'listener', display_name: 'Listener', profile_picture: null,
    playlists: [{ id: 'p1', name: 'Test playlist', total_tracks: 2, image: null,
      owner: { id: 'listener', display_name: 'Listener' } }],
  } }));
  await page.route('https://prices.test/get_tracks/p1', route => route.fulfill({ json: tracks }));
  await page.goto('/#session=fake-session');
  await page.getByText('Test playlist', { exact: true }).click();
  const modal = page.getByRole('dialog');
  await expect(modal.getByText('Blinding Lights', { exact: true })).toBeVisible();
  return modal;
}

function priceRow(track) {
  return { track_name: track.name, artist: track.artist,
    itunes_price: 1.29, itunes_url: '', bandcamp_price: -1, bandcamp_url: '',
    beatport_price: 1.49, beatport_url: '' };
}

test('ripple stays visible as per-track prices arrive, then disappears', async ({ page }) => {
  const pending = [];
  await page.route('https://prices.test/db_results', route => { pending.push(route); });
  const modal = await openPlaylist(page);
  await modal.getByRole('button', { name: 'View Prices', exact: true }).click();
  const status = modal.getByRole('status');
  await expect(status).toHaveText('Looking up prices: 0/2');
  await expect(status.locator('span')).toHaveCount(2); // Both animated ripple rings.
  await expect(modal.getByRole('button', { name: 'Looking Up Prices…' })).toBeDisabled();
  await expect.poll(() => pending.length).toBe(1);
  expect(pending[0].request().postDataJSON()).toEqual({ tracks: [tracks[0]] });
  await pending[0].fulfill({ json: [priceRow(tracks[0])] });
  await expect(status).toHaveText('Looking up prices: 1/2');
  await expect(modal.getByRole('row').filter({ hasText: 'Blinding Lights' })).toContainText('$1.29');
  await expect(modal.getByRole('row').filter({ hasText: 'Deja Vu' })).not.toContainText('$1.29');
  await expect.poll(() => pending.length).toBe(2);
  expect(pending[1].request().postDataJSON()).toEqual({ tracks: [tracks[1]] });
  await pending[1].fulfill({ json: [priceRow(tracks[1])] });
  await expect(status).toHaveCount(0);
  await expect(modal.getByRole('button', { name: 'View Playlist' })).toBeEnabled();
  await expect(modal.getByRole('row').filter({ hasText: 'Deja Vu' })).toContainText('$1.29');
});

test('request failure removes ripple and enables retry without discarding completed prices', async ({ page }) => {
  let requests = 0;
  await page.route('https://prices.test/db_results', route => {
    requests++;
    return requests === 1
      ? route.fulfill({ json: [priceRow(tracks[0])] })
      : route.fulfill({ status: 503, json: { error: 'Store unavailable' } });
  });
  const modal = await openPlaylist(page);
  await modal.getByRole('button', { name: 'View Prices', exact: true }).click();
  await expect(modal.getByRole('alert')).toContainText('Some prices could not be fetched');
  await expect(modal.getByRole('status')).toHaveCount(0);
  await expect(modal.getByRole('button', { name: 'Retry Prices' })).toBeEnabled();
  await expect(modal.getByRole('row').filter({ hasText: 'Blinding Lights' })).toContainText('$1.29');
});

test('provider error removes ripple and keeps successful store prices', async ({ page }) => {
  await page.route('https://prices.test/db_results', route => {
    const [track] = route.request().postDataJSON().tracks;
    return route.fulfill({ json: [{ ...priceRow(track), errors: ['bandcamp'] }] });
  });
  const modal = await openPlaylist(page);
  await modal.getByRole('button', { name: 'View Prices', exact: true }).click();
  await expect(modal.getByRole('alert')).toContainText('Some stores could not be reached');
  await expect(modal.getByRole('status')).toHaveCount(0);
  await expect(modal.getByRole('button', { name: 'Retry Prices' })).toBeEnabled();
  await expect(modal.getByRole('row').filter({ hasText: 'Blinding Lights' })).toContainText('$1.49');
});

test.describe('store last-checked dates', () => {
  test.use({ locale: 'en-US', timezoneId: 'America/Denver' });

  test('shows each store date in local time as prices arrive and hides unchecked dates', async ({ page }) => {
    const pending = [];
    await page.route('https://prices.test/db_results', route => { pending.push(route); });
    const modal = await openPlaylist(page);
    await modal.getByRole('button', { name: 'View Prices', exact: true }).click();
    await expect(modal.locator('time')).toHaveCount(0);
    await expect.poll(() => pending.length).toBe(1);
    await pending[0].fulfill({ json: [{
      ...priceRow(tracks[0]),
      // UTC Oct 18 is still Oct 17 in the browser's timezone.
      itunes_validated_at: '2026-10-18T01:30:00+00:00',
      itunes_url: 'https://itunes.example/song',
      bandcamp_validated_at: '2026-10-16T18:00:00+00:00',
      beatport_validated_at: null,
    }] });
    await expect(modal.getByRole('status')).toHaveText('Looking up prices: 1/2');
    const firstCells = modal.getByRole('row').filter({ hasText: 'Blinding Lights' }).getByRole('cell');
    await expect(firstCells.nth(1)).toHaveText('N/A checked Oct 16');
    await expect(firstCells.nth(2)).toHaveText('$1.49');
    await expect(firstCells.nth(3).locator('time')).toHaveText('checked Oct 17');
    await expect(firstCells.nth(3).getByRole('link', { name: '$1.29' })).toHaveAttribute('href', 'https://itunes.example/song');
    await expect(firstCells.nth(3).locator('time')).toHaveAttribute('datetime', '2026-10-18T01:30:00+00:00');
    await expect(modal.getByRole('row').filter({ hasText: 'Deja Vu' }).locator('time')).toHaveCount(0);

    await expect.poll(() => pending.length).toBe(2);
    await pending[1].fulfill({ json: [{
      ...priceRow(tracks[1]),
      bandcamp_price: 0,
      bandcamp_validated_at: '2026-10-17T20:00:00+00:00',
      itunes_validated_at: 'invalid-date',
      // An older API response may omit the timestamp entirely.
    }] });
    await expect(modal.getByRole('status')).toHaveCount(0);
    const secondCells = modal.getByRole('row').filter({ hasText: 'Deja Vu' }).getByRole('cell');
    await expect(secondCells.nth(1)).toHaveText('$0.00 checked Oct 17');
    await expect(secondCells.nth(2).locator('time')).toHaveCount(0);
    await expect(secondCells.nth(3).locator('time')).toHaveCount(0);
    await expect(firstCells.nth(3).locator('time')).toHaveText('checked Oct 17');
    await expect(modal.getByRole('button', { name: 'View Playlist' })).toBeEnabled();
  });
});

test('one discovery serves StrictMode, profile and playlist filters', async ({ page }) => {
  let reads = 0;
  await page.route('https://prices.test/get_playlists', route => {
    reads++;
    expect(route.request().headers().authorization).toBe('Bearer fake-session');
    return route.fulfill({ json: {
      id: 'listener', display_name: 'Listener', profile_picture: null,
      playlists: [
        { id: 'p1', name: 'My playlist', total_tracks: 2, image: null, owner: { id: 'listener' } },
        { id: 'p2', name: 'Shared playlist', total_tracks: 2, image: null, owner: { id: 'other' } },
      ],
    } });
  });
  await page.goto('/#session=fake-session');
  await expect(page.getByText('My playlist', { exact: true })).toBeVisible();
  await page.locator('input[value="All Playlists"]').click();
  await page.getByRole('option', { name: 'Your Playlists', exact: true }).click();
  await expect(page.getByText('Shared playlist', { exact: true })).toHaveCount(0);
  await expect(page.getByText('My playlist', { exact: true })).toBeVisible();
  await page.locator('input[value="Your Playlists"]').click();
  await page.getByRole('option', { name: 'All Playlists', exact: true }).click();
  await expect(page.getByText('Shared playlist', { exact: true })).toBeVisible();
  expect(reads).toBe(1);
});

test('Apple cooldown shows browser prices and retries the same authenticated track', async ({ page }) => {
  let calls = 0;
  let appleRetry;
  await page.route('https://prices.test/db_results', route => {
    calls++;
    expect(route.request().headers().authorization).toBe('Bearer fake-session');
    const [track] = route.request().postDataJSON().tracks;
    if (calls <= 2) expect(track).toEqual(tracks[0]);
    if (calls === 1) {
      return route.fulfill({ json: [{ ...priceRow(track), itunes_price: -1, errors: ['itunes'], itunes_retry_after: 1 }] });
    }
    if (calls === 2) { appleRetry = route; return; }
    return route.fulfill({ json: [priceRow(track)] });
  });
  const modal = await openPlaylist(page);
  await modal.getByRole('button', { name: 'View Prices', exact: true }).click();
  await expect.poll(() => calls).toBe(2);
  await expect(modal.getByRole('status')).toHaveText('Looking up prices: 0/2');
  const firstRow = modal.getByRole('row').filter({ hasText: 'Blinding Lights' });
  await expect(firstRow).toContainText('$1.49');
  await expect(firstRow).not.toContainText('$1.29');
  await expect(modal.getByRole('alert')).toHaveCount(0);
  await appleRetry.fulfill({ json: [priceRow(tracks[0])] });
  await expect(modal.getByRole('status')).toHaveCount(0);
  await expect(modal.getByRole('alert')).toHaveCount(0);
  await expect(firstRow).toContainText('$1.29');
  expect(calls).toBe(3);
});
