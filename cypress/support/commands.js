// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
Cypress.Commands.add("login", (username, password) => {
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
                username: username,
                password: password,
            },
            headers: {
                "X-CSRFTOKEN": token,
            },
            followRedirect: false
        }).then(response => {
            expect(response.status).to.eql(302)
            expect(response.headers).to.have.property('location')
            expect(response.headers.location).to.not.contain('login')
        })
    });
})
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })
