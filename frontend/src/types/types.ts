export interface Playlist {
  id: string;
  name: string;
  image: string | null;
  total_tracks: number;
  owner?: {
    id: string;
    display_name?: string;
  };
}

  
  export interface User {
    display_name: string;
    profile_picture: string | null;
  }
  