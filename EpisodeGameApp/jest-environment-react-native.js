const { TestEnvironment } = require('jest-environment-node');

class ReactNativeEnvironment extends TestEnvironment {
  constructor(config, context) {
    super(config, context);
    
    // Define React Native globals
    this.global.__DEV__ = true;
    this.global.__BUNDLE_START_TIME__ = Date.now();
    this.global.process = this.global.process || {};
    this.global.process.env = this.global.process.env || {};
    this.global.process.env.NODE_ENV = 'test';
  }

  async setup() {
    await super.setup();
  }

  async teardown() {
    await super.teardown();
  }
}

module.exports = ReactNativeEnvironment;