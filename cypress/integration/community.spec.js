/// <reference types="cypress" />
// Tests the functionality from the Community member perspective

describe("Community members", () => {
    beforeEach(() => {

        cy.visit(Cypress.env('login_url'));
        cy.get("[name=csrfmiddlewaretoken]")
            .should("exist")
            .should("have.attr", "value")
            .as("csrfToken");

        cy.get("@csrfToken").then((token) => {
            cy.request({
                method: "POST",
                url: Cypress.env("login_url"),
                form: true,
                body: {
                    username: "community",
                    password: "1234567890",
                },
                headers: {
                    "X-CSRFTOKEN": token,
                },
            });
        });
    })

    it("can mark a translation as good or bad", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="yes-button"]')
                    .should('be.visible')
                    .click()
                    .should('have.css', 'background-color', 'rgba(102, 142, 63, 0.5)')

                cy.get('[data-cy="no-button"]')
                    .should('be.visible')
                    .click()
                    .should('have.css', 'background-color', 'rgba(215, 130, 120, 0.5)')
            })
    })

    it("can mark a recording as good or bad", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="good-button"]:first')
                    .should('be.visible')
                    .click()
                    .should('have.css', 'background-color', 'rgba(102, 142, 63, 0.5)')

                cy.get('[data-cy="bad-button"]:first')
                    .should('be.visible')
                    .click()
                    .should('have.css', 'background-color', 'rgba(215, 130, 120, 0.5)')
            })
    })
})