/// <reference types="cypress" />
// Tests the functionality from the Linguist perspective

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
                    username: "linguist",
                    password: "1234567890",
                },
                headers: {
                    "X-CSRFTOKEN": token,
                },
            });
        });
    })

    it("can view the advanced options", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="options-button"]')
                    .should('be.visible')
                    .click()

                cy.location('pathname')
                    .should('include', Cypress.env("segment_details_url"))
            })
    })

})