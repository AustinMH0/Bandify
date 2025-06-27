describe('Playlist Flow - Mocked Backend', () => {
  beforeEach(() => {

    cy.intercept('GET', 'http://localhost:5000/get_playlists', {
      statusCode: 200,
      body: {
        display_name: 'Test User',
        profile_picture: null,
        playlists: [
          {
            id: 'test_playlist_123',
            name: 'Test Playlist',
            total_tracks: 2,
            image: 'https://picsum.photos/200/300'
          }
        ]
      }
    }).as('mockGetPlaylists');


    cy.intercept('GET', 'http://localhost:5000/get_tracks/test_playlist_123', {
      statusCode: 200,
      body: [
        { name: 'Test Song 1', artist: 'Test Artist 1' },
        { name: 'Test Song 2', artist: 'Test Artist 2' }
      ]
    }).as('mockGetTracks');

    cy.visit('http://localhost:5173/');
  });

  it('loads playlists and shows track(s) when clicked', () => {
    cy.wait('@mockGetPlaylists');
    cy.contains('Test Playlist').click();

    cy.wait('@mockGetTracks');
    cy.contains('Test Song 1');
    cy.contains('Test Song 2');
  });
});