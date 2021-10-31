// Tests the ability to edit a segment

describe("Edit segment", () => {
    beforeEach(() => {
        cy.login("linguist", "1234567890");
    })

    it("shows original word", () => {
        
        cy.visit(Cypress.env('maskwacis'));

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
                    .should('include', Cypress.env("awas_url"))
            })


        cy.get("#segment-table").within(() => {
            cy.get('@transcription')
        })
    })
    
    it("shows all tables", () => {
        cy.visit(Cypress.env("awas_url"));

        cy.get("#segment-table").within(() => {
            cy.get('th').contains('Transcription')
            cy.get('th').contains('Translation')
            cy.get('th').contains('Analysis')
            cy.get('th').contains('Recordings')
            cy.get('th').contains('Speaker')
        })

        cy.get("#suggestions-table").within(() => {
            cy.get('th').contains('Suggestion')
            cy.get('th').contains('Translation')
            cy.get('th').contains('Analysis')
            cy.get('th').contains('Source')
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
            .should('be.visible')
    })

    it("shows all buttons", () => {
        cy.visit(Cypress.env("awas_url"));

        cy.get("#suggestions-table").within(() => {
            cy.get('input:first')
                .should('have.value', 'Accept')
        })
    })

    it("should load content when clicking Accept", () => {
        cy.visit(Cypress.env("awas_url"));

        cy.get("#suggestions-table").within(() => {
            cy.get('[data-cy="suggestion-transcription"]')
                .first()
                .invoke('text')
                .as('transcription')
            cy.get('[data-cy="suggestion-analysis"]')
                .first()
                .invoke('text')
                .as('analysis')
            cy.get('input:first')
                .should('have.value', 'Accept')
                .click()

            
        })
        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_source_language')
            .should('be.visible')
            .within(() => {
                cy.get('@transcription')
            })

        cy.get('#id_analysis')
            .should('be.visible')
            .within(() => {
                cy.get('@analysis')
            })
    })

    it("should load edit div", () => {
        cy.visit(Cypress.env("awas_url"));

        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_source_language')
            .should('be.visible')

        cy.get('#id_translation')
            .should('be.visible')
    })

    it("should update the entry when clicking Save", () => {
        cy.visit(Cypress.env("awas_url"));

        cy.get("#suggestions-table").within(() => {
            cy.get('[data-cy="suggestion-transcription"]')
                .first()
                .invoke('text')
                .as('transcription')
            cy.get('[data-cy="suggestion-analysis"]')
                .first()
                .invoke('text')
                .as('analysis')
            cy.get('input:first')
                .should('have.value', 'Accept')
                .click()
        })
        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_source_language')
            .should('be.visible')
            .within(() => {
                cy.get('@transcription')
            })

        cy.get('#id_analysis')
            .should('be.visible')
            .within(() => {
                cy.get('@analysis')
            })

        cy.get('[data-cy="save-button"]')
            .click()

        cy.get("#segment-table").within(() => {
            cy.get('@transcription')
            cy.get('@analysis')
        })

        // Make sure the username of the editor was stored
        cy.get("#revision-table")
            .contains('linguist')
    })
    
    it("should load content when clicking Revert", () => {
        cy.visit(Cypress.env("awas_url"));

        cy.get("#revision-table").within(() => {
            cy.get('[data-cy="revision-transcription"]')
                .first()
                .invoke('text')
                .as('transcription')
            cy.get('[data-cy="revision-analysis"]')
                .first()
                .invoke('text')
                .as('analysis')
            cy.get('input:first')
                .should('have.value', 'Revert')
                .click()
        })

        cy.get('[data-cy=edit-div]').should('be.visible')
        cy.get('#id_source_language')
            .should('be.visible')
            .within(() => {
                cy.get('@transcription')
            })

        cy.get('#id_analysis')
            .should('be.visible')
            .within(() => {
                cy.get('@analysis')
            })
    })
});

describe("Edit segment, no auth", () => {
    it("can not see details page", () => {
        
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {

                cy.get('[data-cy="options-button"]')
                    .should('not.exist')
            })
    })
})
