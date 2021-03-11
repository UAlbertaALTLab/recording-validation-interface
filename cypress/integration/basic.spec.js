/// <reference types="cypress" />
// Tests that the basic UI loads

describe("On load", () => {
    it("shows all the basic information", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .as('card')
            .should('be.visible')

        cy.get('[data-cy="card-header"]')
            .should('be.visible')
            .within(() => {
                cy.get('@card')
            })

        cy.get('[data-cy="transcription"]')
            .should('be.visible')
            .within(() => {
                cy.get('@card')
            })

        cy.get('[data-cy="translation"]')
            .should('be.visible')
            .within(() => {
                cy.get('@card')
            })

        cy.get('[data-cy="recording"]')
            .should('be.visible')
            .within(() => {
                cy.get('@card')
            })

        cy.get('[data-cy="speaker"]')
            .should('be.visible')
            .within(() => {
                cy.get('@card')
            })

        cy.get('[data-cy="nav-button"]')
            .should('be.visible')
    })
})