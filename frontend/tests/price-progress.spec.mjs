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
