// Tests the single word view page

describe("Details View", () => {
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

    it("clicks on options button", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="options-button"]')
                    .click()

                cy.location('pathname')
                    .should('include', Cypress.env("segment_details_url"))
            })
    })

    it("shows original word", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {
                cy.get('[data-cy="transcription"]')
                    .invoke('text')
                    .as('transcription')

                 cy.get('[data-cy="translation"]')
                     .invoke('text')
                    .as('translation')

                cy.get('[data-cy="options-button"]')
                    .click()

                cy.location('pathname')
                    .should('include', Cypress.env("segment_details_url"))
            })


        cy.get("#segment-table").within(() => {
            cy.get('@transcription')
            cy.get('@translation')
        })

    })

    it("shows both tables with headers", () => {
        cy.visit(Cypress.env('home'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {
                cy.get('[data-cy="options-button"]')
                    .click()

                cy.location('pathname')
                    .should('include', Cypress.env("segment_details_url"))
            })

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