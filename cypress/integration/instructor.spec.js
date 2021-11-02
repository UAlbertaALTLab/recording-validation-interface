// Tests the functionality from the Instructor perspective

describe("Instructors", () => {
    before(() => {
        cy.login("instructor", "1234567890");
    })

    it("can flag entries", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="flag-button"]')
                    .click()

                cy.get('[data-cy="modal"]')
                    .should('be.visible')
            })
    })
})
