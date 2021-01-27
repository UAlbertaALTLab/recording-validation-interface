/// <reference types="cypress" />
// Tests for register UI functionality

describe("Register", () => {
    it("loads from login page", () => {
        // checks that register button on login page
        // navigates to register page
        cy.visit('/login')

        cy.get('#register-button')
            .should('be.visible')
            .click();

        cy.location('pathname')
            .should('include', 'register')
    })

    it("loads all UI elements", () => {
        // checks that all UI elements load
        cy.visit('/register')

        cy.get('h2')
            .contains('Register as a New User')

        cy.get('#register-form')
            .should('be.visible');

        cy.get('#id_first_name')
            .should('be.visible');

        cy.get('#id_last_name')
            .should('be.visible');

        cy.get('#id_username')
            .should('be.visible');

        cy.get('#id_password')
            .should('be.visible');

        cy.get('#register-button')
            .should('be.visible');
    })

    it("creates a new valid user", () => {
        // creates a new valid user
        cy.visit('/register')

        cy.get('h2')
            .contains('Register as a New User')

        cy.get('#register-form')
            .should('be.visible');

        cy.get('#id_first_name')
            .type('First');

        cy.get('#id_last_name')
            .type('Last');

        cy.get('#id_username')
            .type('test_user');

        cy.get('#id_password')
            .type('password');

        cy.get('#register-button')
            .click();

        cy.location('pathname')
            .should('include', 'login')
    })

    it("raises an error when the username is already taken", () => {
        // doesn't allow username duplication
        cy.visit('/register')

        cy.get('h2')
            .contains('Register as a New User')

        cy.get('#register-form')
            .should('be.visible');

        cy.get('#id_first_name')
            .type('First');

        cy.get('#id_last_name')
            .type('Last');

        cy.get('#id_username')
            .type('jpoulin');

        cy.get('#id_password')
            .type('password');

        cy.get('#register-button')
            .click();

        cy.location('pathname')
            .should('include', 'register')

        cy.get('.errorlist')
            .should('be.visible')
            .should('contain', 'Username is already taken.')
    })

    it("needs a first name to make a new user", () => {
        cy.visit('/register')

        cy.get('h2')
            .contains('Register as a New User')

        cy.get('#register-form')
            .should('be.visible');

        cy.get('#register-button')
            .click();

        cy.location('pathname')
            .should('include', 'register')

    })

    it("needs a last name to make a new user", () => {
        cy.visit('/register')

        cy.get('h2')
            .contains('Register as a New User')

        cy.get('#register-form')
            .should('be.visible');

        cy.get('#id_first_name')
            .type('First');

        cy.get('#register-button')
            .click();

        cy.location('pathname')
            .should('include', 'register')

    })

    it("needs a username to make a new user", () => {
        cy.visit('/register')

        cy.get('h2')
            .contains('Register as a New User')

        cy.get('#register-form')
            .should('be.visible');

        cy.get('#id_first_name')
            .type('First');

        cy.get('#id_last_name')
            .type('Last');

        cy.get('#register-button')
            .click();

        cy.location('pathname')
            .should('include', 'register')

    })

    it("needs a password to make a new user", () => {
        cy.visit('/register')

        cy.get('h2')
            .contains('Register as a New User')

        cy.get('#register-form')
            .should('be.visible');

        cy.get('#id_first_name')
            .type('First');

        cy.get('#id_last_name')
            .type('Last');

        cy.get('#id_username')
            .type('new_user');

        cy.get('#register-button')
            .click();

        cy.location('pathname')
            .should('include', 'register')
    })

})