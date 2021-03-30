// Tests the functionality from the Community member perspective

describe("Language experts", () => {
    beforeEach(() => {
        cy.login("expert", "1234567890");
    })

    it("can mark a translation as good or bad", () => {
        cy.visit(Cypress.env('home'));

        let customGreen = null;

        cy.window()
            .then((win) => {
                customGreen = win.getComputedStyle(win.document.documentElement).getPropertyValue('--custom-pale-green');
            })

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="yes-button"]')
                    .click()
                    .should('have.class', 'button--success-solid')

                cy.get('[data-cy="no-button"]')
                    .click()
                    .should('have.class', 'button--fail-solid')
            })
    })

    it("can mark a recording as good or bad", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="good-button"]:first')
                    .click()
                    .should('have.class', 'button--success-solid')

                cy.get('[data-cy="bad-button"]:first')
                    .click()
                    .should('have.class', 'button--fail-solid')
            })
    })
})