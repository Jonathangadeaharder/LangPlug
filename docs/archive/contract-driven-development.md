# DEPRECATED: AI Agent Rule File for Contract Driven Development (CDD)

**⚠️ DEPRECATION NOTICE**: This file is deprecated. Use the comprehensive testing strategy documentation instead:

- **Primary Reference**: `docs/TESTING_STRATEGY.md` - Complete testing strategy and CDD implementation
- **Technical Details**: `Backend/tests/CONTRACT_DRIVEN_DEVELOPMENT.md` - Implementation specifics
- **Tooling Reference**: `docs/tooling/contract_and_test_tooling.md` - Updated tooling commands

---

# Original AI Agent Rule File for Contract Driven Development (CDD)

rules:

- name: "Define Clear Interface Contracts Upfront"
  description: >
  All components must expose interfaces defined in a shared contract before implementation.
  This enables proper integration and coordination across independent teams.
  scope: "All components and services development"
  do:
  - "Always generate and use interface contracts before coding."
  - "Validate contracts against shared specifications repositories."
    dont:
  - "Do not start implementation without contract approval."
    rationale: >
    Defining contracts upfront reduces integration issues and clarifies expectations among teams.

- name: "Design by Contract Behavior Guarantees"
  description: >
  Modules must specify guarantees about their behavior through contracts.
  This improves testability and reliability of components.
  scope: "Module and service implementation"
  do:
  - "Always ensure components adhere strictly to the contract guarantees."
  - "Implement automated contract tests to validate behavior."
    dont:
  - "Avoid modifying behavior without corresponding contract updates."
    rationale: >
    Design by contract enforces a robust development process and prevents breaking changes silently.

- name: "Automated Contract Testing"
  description: >
  Convert API specifications (OpenAPI, AsyncAPI, gRPC proto, etc.) into executable contracts.
  Run these tests regularly in CI pipelines to detect integration issues early.
  scope: "Continuous Integration / Continuous Deployment"
  do:
  - "Run contract tests on every code commit."
  - "Fail builds on contract incompatibility."
    dont:
  - "Never bypass contract testing."
    rationale: >
    Automated contract tests shift-left contract validation and ensure the stability of integration points.

- name: "Contract Versioning and Change Management"
  description: >
  Manage contracts versions carefully. Owners must version contracts and communicate changes.
  This avoids unexpected breaking changes downstream.
  scope: "All contract definitions and shared repositories"
  do:
  - "Use semantic versioning for contract changes."
  - "Notify dependent teams about breaking contract changes in advance."
    dont:
  - "Do not modify contracts in backward incompatible ways without version increments."
    rationale: >
    Proper versioning supports independent development and deployment of components.

- name: "Language-Agnostic Contract Usage"
  description: >
  Contracts apply independently of implementation language or stack.
  Teams can choose their technology but must honor the contracts.
  scope: "All development teams and components"
  do:
  - "Respect contracts irrespective of implementation language."
  - "Generate client/server stubs from contracts for consistency."
    dont:
  - "Avoid language-dependent shortcuts that violate contract specifications."
    rationale: >
    Language independence ensures interoperability and flexibility in multi-team environments.

- name: "Enable Team Autonomy via Contracts"
  description: >
  Contracts should allow teams to develop components independently without waiting on others.
  Mocking and stubbing based on contracts enable parallel development.
  scope: "Development teams working on dependent components"
  do:
  - "Create and maintain mocks or fakes based on contract definitions."
  - "Regularly sync test environments with updated contract states."
    dont:
  - "Do not integrate without contract synchronization."
    rationale: >
    Independent development improves velocity and reduces bottlenecks.

- name: "Enforce Contract Review and Approval"
  description: >
  All contract changes must go through formal review before implementation.
  This ensures consensus and reduces integration conflicts.
  scope: "Contract modification lifecycle"
  do:
  - "Require peer and stakeholder approval for contract changes."
  - "Document rationale and impact for contract updates."
    dont:
  - "Never skip contract review steps."
    rationale: >
    Review processes uphold contract quality and team alignment.

# End of rules
