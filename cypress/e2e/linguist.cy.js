// Tests the functionality from the Linguist perspective

describe("Linguists", () => {
    beforeEach(() => {
        cy.login("linguist", "1234567890");
    })

    it("can view the advanced options", () => {
        cy.visit(Cypress.env('maskwacis'));

        cy.get('[data-cy="segment-card"]:first')
            .within(() => {
                cy.get('[data-cy="card-header"]').should('have.attr', 'data-phrase-id')
                .then((id) => {
                    cy.get('[data-cy="options-button"]')
                        .click()

                    cy.location('pathname')
                        .should('include', Cypress.env("segment_url")+id)
                })
            })
    })

    it("can view all open issues", () => {
        cy.visit(Cypress.env('issues'));

        cy.get('[data-cy="issue-card"]')
            .first()
            .should('be.visible')
    })

    it.only("can resolve an open issue", () => {
        cy.visit(Cypress.env('issues'));
        
        cy.get('[data-cy="issue-card"]')
            .filter(':contains("Recording:")')
            .first()
            .find('[data-cy="more-info-issue-button"]')
            .then(($button) => {
                cy.wrap($button).find('a')
                    .should('have.attr', 'href')
                    .then((old_href) => {
                        cy.wrap($button).click()
                          
                        cy.location('pathname')
                        .should('include', old_href)
                        
                        cy.get('#id_speaker')
                        .select('JER')
    
                        cy.get('[name="phrase"]')
                            .click()
                            .type("hello")
    
                        cy.get('[data-cy=save-button]')
                            .click()
    
                        cy.location('pathname')
                            .should('include', '/issues')
                
                        // Now make sure the issue is gone
                        cy.visit(Cypress.env('issues'));
                        cy.get('[data-cy="issue-card"]').find('a')
                            .should("have.attr", 'href')
                            .should("not.contain", old_href)  
                    })
            })
    })

    it("can close an open issue", () => {
        cy.visit(Cypress.env('issues'));

        cy.get('[data-cy="issue-card"]')
            .first()
            .within(() => {
                cy.get('[data-cy=close-issue-button]')
                    .click()
            })
    })

})
