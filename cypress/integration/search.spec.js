/// <reference types="cypress" />
// Tests for search and advanced search

describe("Search", () => {
    it("should search for then display the first word on the main page", () => { 
        cy.visit(Cypress.env("home"))

        cy.get('a[name="word-link"]:first')
            .then((anchorElements) => {
                const word = anchorElements[0].id
                cy.get("input[name='query']")
                    .click()
                    .type(word)
                    .type('{enter}')

                cy.get('h2')
                    .contains(word)
                
                cy.get(".table")
                    .should("be.visible")
                    .contains("Transcription")
                cy.get(".table")
                    .contains("Translation")
                cy.get(".table")
                    .contains("Recordings")
                cy.get(".table")
                    .contains(word)
            })
    })

})

describe("Advanced Search", () => {
    it("should display the advanced search results", () => { 
        cy.visit(Cypress.env("home"))

        cy.get('[data-cy="advanced-search-button"]')
            .click()

        cy.get("input[name='transcription']")
            .click()
            .type('kwâskwêpitêw')

        cy.get("input[name='translation']")
            .click()
            .type('hook')

        cy.get('[data-cy="advanced-form-submit"]')
            .click()

        cy.get('h2')
            .contains("advanced search")
        
        cy.get(".table")
            .should("be.visible")
            .contains("Transcription")
        cy.get(".table")
            .contains("Translation")
        cy.get(".table")
            .contains("Recordings")
        cy.get(".table")
            .contains("kwâskwêpitêw")
        cy.get(".table")
            .contains("hook")
    })

    // TODO: add tests for analysis matching, validation state matching,
    // and speaker matchings
})