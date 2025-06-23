import { Select } from "@mantine/core";
import { useEffect } from "react";
import { useLocalStorage } from "@mantine/hooks"; // ✅ Import the hook
import type { Playlist } from "../../types/types";

interface PlaylistSortProps {
  playlists: Playlist[];
  setPlaylists: React.Dispatch<React.SetStateAction<Playlist[]>>;
  originalPlaylists: Playlist[];
  userId: string | undefined;
}

const PlaylistSort = ({
  playlists,
  setPlaylists,
  originalPlaylists,
  userId,
}: PlaylistSortProps) => {
  // ✅ Use local storage for filter and sort options
  const [filterOption, setFilterOption] = useLocalStorage<"all" | "user">({
    key: "playlist-filter",
    defaultValue: "all",
  });

  const [sortOption, setSortOption] = useLocalStorage<string>({
    key: "playlist-sort",
    defaultValue: "recent",
  });

  useEffect(() => {
    let filtered = [...originalPlaylists];

    if (filterOption === "user") {
      filtered = filtered.filter((p) => p.owner?.id === userId);
    }

    switch (sortOption) {
      case "name-asc":
        filtered.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case "name-desc":
        filtered.sort((a, b) => b.name.localeCompare(a.name));
        break;
      case "oldest":
        filtered.reverse();
        break;
      case "recent":
      default:
        break;
    }

    setPlaylists(filtered);
  }, [sortOption, filterOption, originalPlaylists, userId]);

  return (
    <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginBottom: "1rem" }}>
      <Select
        label="Sort by"
        value={sortOption}
        onChange={(value) => {
          if (value) setSortOption(value);
        }}
        data={[
          { value: "recent", label: "Recently Added" },
          { value: "name-asc", label: "Name (A–Z)" },
          { value: "name-desc", label: "Name (Z–A)" },
          { value: "oldest", label: "Oldest" },
        ]}
        clearable={false}
        maw={200}
      />

      <Select
        label="Filter"
        value={filterOption}
        onChange={(value) => {
          if (value === "user" || value === "all") {
            setFilterOption(value);
          }
        }}
        data={[
          { value: "all", label: "All Playlists" },
          { value: "user", label: "Your Playlists" },
        ]}
        clearable={false}
        maw={200}
      />
    </div>
  );
};

export default PlaylistSort;
