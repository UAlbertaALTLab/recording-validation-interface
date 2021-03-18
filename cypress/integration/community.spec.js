// Tests the functionality from the Community member perspective

describe("Community members", () => {
    beforeEach(() => {
        cy.login("community", "1234567890");
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
                    .should('have.css', 'background-color', 'rgba(102, 142, 63, 0.5)')

                cy.get('[data-cy="no-button"]')
                    .click()
                    .should('have.css', 'background-color', 'rgba(215, 130, 120, 0.5)')
            })
    })

    it("can mark a recording as good or bad", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="good-button"]:first')
                    .click()
                    .should('have.css', 'background-color', 'rgba(102, 142, 63, 0.5)')

                cy.get('[data-cy="bad-button"]:first')
                    .click()
                    .should('have.css', 'background-color', 'rgba(215, 130, 120, 0.5)')
            })
    })
})