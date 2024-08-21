const { defineConfig } = require('cypress')

module.exports = defineConfig({
  env: {
    home: '/',
    maskwacis: '/maskwacis/entries',
    login_url: '/login',
    register_url: '/register',
    logout_url: '/logout',
    issues: '/maskwacis/issues',
    segment_details_url: '/maskwacis/segment/146',
    segment_url: '/maskwacis/segment/',
    awas_url: '/maskwacis/segment/6',
  },
  e2e: {
    // We've imported your old cypress plugins here.
    // You may want to clean this up later by importing these.
    setupNodeEvents(on, config) {
      return require('./cypress/plugins/index.js')(on, config)
    },
    baseUrl: 'http://localhost:8000',
  },
})
