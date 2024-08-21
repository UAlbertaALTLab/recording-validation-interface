// Tests for search and advanced search

describe("Search", () => {
    it("should search for then display the first word on the main page", () => { 
        cy.visit(Cypress.env("maskwacis"))
        let word = 'awas'

        cy.get('[data-cy="search-bar"]')
            .click()
            .type(word)
            .type('{enter}')

        cy.get('h2')
            .contains(word)

        cy.get('[data-cy="segment-card"]')
            .should("be.visible")
            .contains(word)
    })

})

describe("Advanced Search", () => {
    it("should display the advanced search results", () => {
        cy.visit(Cypress.env("maskwacis"))

        cy.get('[data-cy="advanced-search-button"]')
            .click()

        cy.get("input[name='transcription']")
            .click()
            .type('awas')

        cy.get("input[name='translation']")
            .click()
            .type('Slough')

        cy.get('[data-cy="advanced-form-submit"]')
            .click()

        cy.get('h2')
            .contains("advanced search")

        cy.get('[data-cy="segment-card"]')
            .should("be.visible")
            .contains('awas')
    })

    // TODO: add tests for analysis matching, validation state matching,
    // and speaker matchings
})
