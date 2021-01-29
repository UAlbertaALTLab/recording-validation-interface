/// <reference types="cypress" />
// Tests the single word view page

describe("Details View", () => {
    it("clicks on word", () => {
        cy.visit(Cypress.env('home'));

        cy.get(".table")
            .should("be.visible");

        cy.get('a[name="word-link"]:first')
            .click();

        cy.location('pathname')
            .should('include', 'segment/1');
    })

    it("shows original word", () => {
        cy.visit(Cypress.env('home'));

        cy.get(".table")
            .should("be.visible");

        cy.get('a[name="word-link"]:first')
            .then((word) => {
                const w = word[0].id
                cy.get('a[name="word-link"]:first')
                    .click()

                cy.location('pathname')
                    .should('include', 'segment/1');

                cy.get('#segment-table')
                    .contains(w)
            })

        cy.get("#segment-table").within(() => {
            cy.get('th').contains('Transcription')
            cy.get('th').contains('Translation')
            cy.get('th').contains('Recordings')
            cy.get('th').contains('Speaker')
        })

    })

    it("shows both tables with headers", () => {
        cy.visit(Cypress.env('home'));

        cy.get(".table")
            .should("be.visible");

        cy.get('a[name="word-link"]:first')
            .click()

        cy.get("#segment-table").within(() => {
            cy.get('th').contains('Transcription')
            cy.get('th').contains('Translation')
            cy.get('th').contains('Recordings')
            cy.get('th').contains('Speaker')
        })

        cy.get("#suggestions-table").within(() => {
            cy.get('th').contains('Suggestion')
            cy.get('th').contains('Translation')
            cy.get('th').contains('Analysis')
            cy.get('th').contains('MED')
        })

    })
})