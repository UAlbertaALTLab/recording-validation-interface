// Tests the functionality from the Linguist perspective

describe("Linguists", () => {
    beforeEach(() => {
        cy.login("linguist", "1234567890");
    })

    it("can view the advanced options", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="options-button"]')
                    .click()

                cy.location('pathname')
                    .should('include', Cypress.env("awas_url"))
            })
    })

    it("can view all open issues", () => {
        cy.visit(Cypress.env('issues'));

        cy.get('[data-cy="issue-card"]')
            .first()
            .should('be.visible')
    })

    it("can resolve an open issue", () => {
        cy.visit(Cypress.env('issues'));

        cy.get('[data-cy="issue-card"]')
            .first()
            .within(() => {
                cy.get('[data-cy="more-info-issue-button"]')
                    .click()
            })

        cy.location('pathname')
            .should('include', '/issues/1')

        cy.get('#id_speaker')
            .select('JER')

        cy.get('#id_phrase')
            .click()
            .type("hello")

        cy.get('[data-cy=save-button]')
            .click()

        cy.location('pathname')
            .should('include', '/issues')
    })

    it("can close an open issue", () => {
        cy.visit(Cypress.env('issues'));

        cy.get('[data-cy="issue-card"]')
            .first()
            .within(() => {
                cy.get('[data-cy=close-issue-button]')
                    .click()
            })
    })

})
