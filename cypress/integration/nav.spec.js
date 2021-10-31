// Tests the navigation

describe("Navigation", () => {
    it("can use buttons", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="nav-next"]')
            .click()

        cy.url()
            .should('include', "?page=2")

        cy.get('[data-cy="nav-prev"]')
            .click()

        cy.url()
            .should('include', "?page=1")

        cy.get('[data-cy="nav-last"]')
            .click()

        cy.url()
            .should('include', "?page=2")

        cy.get('[data-cy="nav-first"]')
            .click()

        cy.url()
            .should('include', "?page=1")
    })

    it("can jump to page", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="page-num-input"]')
            .click()
            .type("2")

        cy.get('[data-cy="go-button-nav"]')
            .click()

        cy.url()
            .should('include', "?page=2")
    })
})
