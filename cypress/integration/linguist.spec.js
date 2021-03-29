// Tests the functionality from the Linguist perspective

describe("Community members", () => {
    beforeEach(() => {
        cy.login("linguist", "1234567890");
        cy.get('#djHideToolBarButton').click();
    })

    it("can view the advanced options", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="options-button"]')
                    .click()

                cy.location('pathname')
                    .should('include', Cypress.env("segment_details_url"))
            })
    })

})