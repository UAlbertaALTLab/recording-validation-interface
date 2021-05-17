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

    it("can mark a recording as having the wrong word", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="wrong-word-button"]')
            .first()
            .click()

        cy.get('[id="wrong_word"]')
            .first()
            .click()
            .type("test")
            .type('{enter}')
    })

    it("can mark a recording as having the wrong speaker", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="wrong-speaker-button"]')
            .first()
            .click()

        cy.get('[data-cy="rec-save-button"]')
            .first()
            .click()
    })
})
