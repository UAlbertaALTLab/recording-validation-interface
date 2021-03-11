/// <reference types="cypress" />
// Tests the functionality from the Instructor perspective

describe("Instructors", () => {
    before(() => {

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
                    username: "instructor",
                    password: "1234567890",
                },
                headers: {
                    "X-CSRFTOKEN": token,
                },
            });
        });
    })

    it("can flag entries", () => {
        // flagging entries isn't supported yet
        this.skip()
    })
})