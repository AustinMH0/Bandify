const { describe } = require("mocha")


describe('Viewing playlist track prices', () => {

  beforeEach(() => {
    cy.visit('http://localhost:5173/')
  })


  it('displays a home page with description(s)', () => {

    cy.get('[class = "_title_yzw6f_221"]').should('have.text', 'A simple tool to compare prices of your favorite tracks')
    cy.get('p').should('have.text', 'Login with Spotify and connect your playlists. Discover the best prices and support artists you love.')

  })

  it('displays a "Get Started" button and redirects to "log in" page', () => {

    cy.get('[data-variant = "outline"]').should('have.text', 'Get Started').click()

    cy.get('[class = "_title_yzw6f_221"]').should('have.text', 'Let\'s get started')
    cy.get('p').should('have.text', 'We’ll fetch your Spotify playlists so you can start comparing track prices across Bandcamp, iTunes, and Beatport.')
    cy.get('[class = "_animatedButton_yzw6f_339 _greenMode_yzw6f_451"]').should('have.text', 'Log in')
  })

})