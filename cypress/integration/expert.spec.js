// Tests the functionality from the Community member perspective

describe("Language experts", () => {
    beforeEach(() => {
        cy.login("expert", "1234567890");
    })

    it("can mark a translation as good or bad", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="yes-button"]')
                    .click()

                cy.get('[data-cy="no-button"]')
                    .click()
            })
    })

    it("can mark a recording as good or bad", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="good-button"]:first')
                    .click()

                cy.get('[data-cy="bad-button"]:first')
                    .click()
            })
    })
})