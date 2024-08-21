// Tests that the basic UI loads

describe("On load", () => {
    it("shows all the basic information", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .should('be.visible')
            .within(() => {
                cy.get('[data-cy="card-header"]')
                    .should('be.visible')

                cy.get('[data-cy="transcription"]')
                    .should('be.visible')

                cy.get('[data-cy="translation"]')
                    .should('be.visible')

                cy.get('[data-cy="recording"]')
                    .should('be.visible')

                cy.get('[data-cy="speaker"]')
                    .should('be.visible')
            })

        cy.get('[data-cy="nav-button-with-query"]')
            .should('be.visible')
    })
})
