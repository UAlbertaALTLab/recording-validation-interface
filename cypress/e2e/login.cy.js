// Tests for login functionality

describe("Login", () => {
    it("loads the page", () => {
        // checks that all page elements load

        cy.visit(Cypress.env('login_url'))
        cy.get('.login__title')
            .should('be.visible')

        cy.get('.login__form')
            .should('be.visible');

        cy.get('#id_username')
            .should('be.visible');

        cy.get('#id_password')
            .should('be.visible');

        cy.get('#login-button')
            .should('be.visible');

        cy.get('#register-button')
            .should('be.visible');
    })

    it("enters valid information", () => {
        // login as valid user works
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

    })

    it("needs a password to proceed", () => {
        // login without password does not work
        cy.visit(Cypress.env('login_url'))

        cy.get('.login__form')
            .should('be.visible');

        cy.get('input[name=username]')
            .type('test')

        cy.get('#login-button')
            .click()

        cy.location('pathname')
            .should('include', 'login')
    })

    it("needs a VALID password to proceed", () => {
        // login with invalid password does not work
        cy.visit(Cypress.env('login_url'))

        cy.get('.login__form')
            .should('be.visible');

        cy.get('input[name=username]')
            .type('test')

        cy.get('input[name=password]')
            .type('password')

        cy.get('#login-button')
            .click()

        cy.location('pathname')
            .should('include', 'login')

    })

    it("needs needs to login with a real user", () => {
        // login with invalid password does not work
        cy.visit(Cypress.env('login_url'))

        cy.get('.login__form')
            .should('be.visible');

        cy.get('input[name=username]')
            .type('fake')

        cy.get('input[name=password]')
            .type('user')

        cy.get('#login-button')
            .click()

        cy.location('pathname')
            .should('include', 'login')

    })
})