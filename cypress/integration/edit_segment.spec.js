/// <reference types="cypress" />
// Tests the ability to edit a segment

describe("Edit segment", () => {
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
              username: "cypress",
              password: "1234asdf",
            },
            headers: {
              "X-CSRFTOKEN": token,
            },
          });
        });
    })

    it("shows original word", () => {
        
        cy.visit(Cypress.env('home'));

        cy.get(".table")
            .should("be.visible");

        cy.get('a[name="word-link"]:first')
            .then((word) => {
                const word_id = word[0].id
                cy.get('a[name="word-link"]:first')
                    .click()

                cy.location('pathname')
                    .should('include', Cypress.env("segment_details_url"));

                cy.get('#segment-table')
                    .contains(word_id)
            })
        })
    
    it("shows all tables", () => {
        cy.visit(Cypress.env("segment_details_url"));

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
            cy.get('th').contains('Options')
        })

        cy.get("#revision-table").within(() => {
            cy.get('th').contains('User')
            cy.get('th').contains('Date')
            cy.get('th').contains('Transcription')
            cy.get('th').contains('Translation')
            cy.get('th').contains('Analysis')
            cy.get('th').contains('Options')
        })

        cy.get('#edit')
                .should('not.be.visible')
    })

    it("shows all buttons", () => {
        cy.visit(Cypress.env("segment_details_url"));

        cy.get("#suggestions-table").within(() => {
            cy.get('input:first')
                .should('have.value', 'Accept')
        })

        cy.get("#revision-table").within(() => {
            cy.get('input:first')
                .should('have.value', 'Revert')
        })

    })

    it("should load content when clicking Accept", () => {
        cy.visit(Cypress.env("segment_details_url"));

        cy.get("#suggestions-table").within(() => {
            cy.get('[cy-data="suggestion-transcription"]')
                .first()
                .invoke('text')
                .as('transcription')
            cy.get('[cy-data="suggestion-translation"]')
                .first()
                .invoke('text')
                .as('translation')
            cy.get('[cy-data="suggestion-analysis"]')
                .first()
                .invoke('text')
                .as('analysis')
            cy.get('input:first')
                .should('have.value', 'Accept')
                .click()

            
        })
        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_cree')
            .should('be.visible')
            .within(() => {
                cy.get('@transcription')
            })

        cy.get('#id_transl')
            .should('be.visible')
            .within(() => {
                cy.get('@translation')
            })

        cy.get('#id_analysis')
            .should('be.visible')
            .within(() => {
                cy.get('@analysis')
            })
    })

    it("should load content when clicking Revert", () => {
        cy.visit(Cypress.env("segment_details_url"));

        cy.get("#revision-table").within(() => {
            cy.get('[cy-data="revision-transcription"]')
                .first()
                .invoke('text')
                .as('transcription')
            cy.get('[cy-data="revision-translation"]')
                .first()
                .invoke('text')
                .as('translation')
            cy.get('[cy-data="revision-analysis"]')
                .first()
                .invoke('text')
                .as('analysis')
            cy.get('input:first')
                .should('have.value', 'Revert')
                .click()
        })

        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_cree')
            .should('be.visible')
            .within(() => {
                cy.get('@transcription')
            })

        cy.get('#id_transl')
            .should('be.visible')
            .within(() => {
                cy.get('@translation')
            })

        cy.get('#id_analysis')
            .should('be.visible')
            .within(() => {
                cy.get('@analysis')
            })
    })

    it("should load content when clicking Edit", () => {
        cy.visit(Cypress.env("segment_details_url"));

        cy.get('[data-cy="edit-button"]')
            .should('be.visible')
            .click()

        cy.get("#segment-table").within(() => {
            cy.get('[cy-data="segment-transcription"]')
                .first()
                .invoke('text')
                .as('transcription')
            cy.get('[cy-data="segment-translation"]')
                .first()
                .invoke('text')
                .as('translation')
        })

        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_cree')
            .should('be.visible')
            .within(() => {
                cy.get('@transcription')
            })

        cy.get('#id_transl')
            .should('be.visible')
            .within(() => {
                cy.get('@translation')
            })
    })

    it("should update the entry when clicking Save", () => {
        cy.visit(Cypress.env("segment_details_url"));

        cy.get("#suggestions-table").within(() => {
            cy.get('[cy-data="suggestion-transcription"]')
                .first()
                .invoke('text')
                .as('transcription')
            cy.get('[cy-data="suggestion-translation"]')
                .first()
                .invoke('text')
                .as('translation')
            cy.get('[cy-data="suggestion-analysis"]')
                .first()
                .invoke('text')
                .as('analysis')
            cy.get('input:first')
                .should('have.value', 'Accept')
                .click()
        })
        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_cree')
            .should('be.visible')
            .within(() => {
                cy.get('@transcription')
            })

        cy.get('#id_transl')
            .should('be.visible')
            .within(() => {
                cy.get('@translation')
            })

        cy.get('#id_analysis')
            .should('be.visible')
            .within(() => {
                cy.get('@analysis')
            })

        cy.get('[data-cy="save-button"]')
            .should('be.visible')
            .click()

        cy.get("#segment-table").within(() => {
            cy.get('@transcription')
            cy.get('@translation')
            cy.get('@analysis')
        })

        // Make sure the username of the editor was stored
        cy.get("#revision-table")
            .contains('cypress')
    })

    it("should not update the entry when clicking Cancel", () => {
        cy.visit(Cypress.env("segment_details_url"));

        cy.get("#suggestions-table").within(() => {
            cy.get('[cy-data="suggestion-transcription"]')
                .first()
                .invoke('text')
                .as('transcription')
            cy.get('[cy-data="suggestion-translation"]')
                .first()
                .invoke('text')
                .as('translation')
            cy.get('[cy-data="suggestion-analysis"]')
                .first()
                .invoke('text')
                .as('analysis')
            cy.get('input:first')
                .should('have.value', 'Accept')
                .click()            
        })

        cy.get("#segment-table").within(() => {
            cy.get('[cy-data="segment-transcription"]')
                .first()
                .invoke('text')
                .as('og_transcription')
            cy.get('[cy-data="segment-translation"]')
                .first()
                .invoke('text')
                .as('og_translation')         
        })

        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_cree')
            .should('be.visible')
            .within(() => {
                cy.get('@transcription')
            })
            .type("DONT SAVE")

        cy.get('#id_transl')
            .should('be.visible')
            .within(() => {
                cy.get('@translation')
            })
            .type("DONT SAVE")

        cy.get('#id_analysis')
            .should('be.visible')
            .within(() => {
                cy.get('@analysis')
            })
            .type("DONT SAVE")

        cy.get('[data-cy="cancel-button"]')
            .should('be.visible')
            .click()

        cy.get("#segment-table").within(() => {
            cy.get('@og_transcription')
            cy.get('@og_translation')
        })
    })
});

describe("Edit segment, no auth", () => {
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
                    .should('include', Cypress.env("segment_details_url"));

                cy.get('#segment-table')
                    .contains(w)
            })
    })

    it("does not show options or edit", () => {
        cy.visit(Cypress.env("segment_details_url"));

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
            cy.get('Options').should('not.exist')
        })

        cy.get("#revision-table").within(() => {
            cy.get('th').contains('User')
            cy.get('th').contains('Date')
            cy.get('th').contains('Transcription')
            cy.get('th').contains('Translation')
            cy.get('th').contains('Analysis')
            cy.get('Options').should('not.exist')
        })

        cy.get('[data-cy="edit-button"]')
            .should('not.exist')
        cy.get('#edit')
            .should('not.be.visible')
    })

})