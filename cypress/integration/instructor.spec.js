// Tests the functionality from the Instructor perspective

describe("Instructors", () => {
    before(() => {
        cy.login("instructor", "1234567890");
    })

    it.skip("can flag entries", () => {
        // flagging entries isn't supported yet
    })
})