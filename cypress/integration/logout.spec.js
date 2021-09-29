// Tests for logout functionality

describe("Logout", () => {

    it("logs out when logged in", () => {
        // TODO: don't make it log in through the UI
        cy.visit(Cypress.env('login_url'))

        cy.get('.login__form')
            .should('be.visible');

        cy.get('input[name=username]')
            .type('expert')

        cy.get('input[name=password]')
            .type('1234567890')

        cy.get('#login-button')
            .click()

        cy.location('pathname')
            .should('not.include', 'login')

        cy.visit(Cypress.env('maskwacis'))

        cy.get('[data-cy="options-button-header"]')
            .click()

        cy.get('#logout-link')
            .click()

        cy.location('pathname')
            .should('include', 'logout')

        cy.get('h2')
            .contains('You are now logged out')
    })

    it("can go directly to the logout page", () => {
        // TODO: don't make it log in through the UI
        cy.visit(Cypress.env('logout_url'))

        cy.get('h2')
            .contains('You are now logged out')
    })
})
