// Tests the functionality from the Community member perspective

describe("Language experts", () => {
    beforeEach(() => {
        cy.login("expert", "1234567890");
    })

    it("can mark a translation as good or bad", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="yes-button"]')
                    .click()

                cy.get('[data-cy="no-button"]')
                    .click()
            })
    })

    it("can mark a recording as good or bad", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="good-button"]:first')
                    .click()

                cy.get('[data-cy="bad-button"]:first')
                    .click()
            })
    })

    it("can mark a recording as having the wrong speaker", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="wrong-speaker-button"]:first')
                    .click()

            })

        cy.get('.modal-dialog:first')
            .within(() => {
                cy.get('[data-cy="rec-save-button"]')
                    .click()
            })
    })

    it("can mark a recording as having the wrong word", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="wrong-word-button"]:first')
                    .click()

                cy.get('#wrong_word:first')
                    .click()
                    .type("hello")

                cy.get('[data-cy="save-wrong-word"]:first')
                    .click()

            })
    })

    it("can cancel marking a recording as having the wrong word", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="wrong-word-button"]:first')
                    .click()

                cy.get('#wrong_word:first')
                    .click()
                    .type("hello")

                cy.get('[data-cy="cancel-wrong-word"]:first')
                    .click()

            })
    })

    it("can flag an entry for review", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy=flag-button]')
                    .click()

                cy.get('[data-cy=save-button]:first')
                    .click()

            })
    })

    it("can cancel flagging an entry for review", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy=flag-button]')
                    .click()

                cy.get('[data-cy=cancel-button]')
                    .click()

            })
    })
})
