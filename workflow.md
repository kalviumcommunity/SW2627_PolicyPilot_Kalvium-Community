# GitHub Team Workflow and Conventions

## 1. Branching Strategy

Our team keeps the `main` branch stable and releasable at all times.

* The `main` branch contains only reviewed and releasable code.
* New features are developed in separate feature branches.
* Feature branches follow the naming convention:

`feature/[short-description]`

* Bug fixes use:

`fix/[short-description]`

* Documentation changes use:

`docs/[short-description]`

* Refactoring uses:

`refactor/[short-description]`

* Maintenance tasks use:

`chore/[short-description]`

Example:

`feature/data-validation`

After a pull request is reviewed and merged, the corresponding branch is deleted to keep the repository clean.

## 2. Commit Message Convention

All commits follow this format:

`[type]: [description]`

The supported commit types are:

* `feat` - new functionality
* `fix` - bug fixes
* `docs` - documentation changes
* `refactor` - code restructuring without changing functionality
* `chore` - maintenance and configuration changes

Examples:

`feat: add data validation`

`docs: document branching strategy`

`chore: update project configuration`

Commit messages should clearly describe what the commit changes.

This convention provides a consistent project history, makes changes easier to understand during code review, and enables automated changelog generation.

## 3. Pull Request Review Process

All changes intended for `main` must be submitted through a Pull Request.

Our review process follows these rules:

* PRs require at least one approval before merging.
* The PR description must explain what changed and why.
* Related GitHub issues must be linked to the PR.
* Commit messages are reviewed as part of the code review process.
* Reviewers focus on:

  * Correctness
  * Code clarity
  * Data integrity
  * Test coverage

The PR should not be merged until the required approval has been received and review comments have been addressed.

## 4. GitHub Issue Tracking

Every new feature or bug fix starts with a GitHub issue.

Each issue should contain:

* A clear action-oriented title
* A description explaining why the work matters
* A definition of what "done" means
* At least one appropriate label
* An assignee responsible for the work

Issues provide context and make responsibilities visible to the team.

When the corresponding Pull Request is successfully merged, the related issue is closed.

## 5. Standard Contribution Workflow

A team member contributing a new feature should:

1. Start from the latest `main` branch.
2. Create an appropriately named feature branch.
3. Implement the required changes.
4. Commit changes using the agreed commit message convention.
5. Push the branch to GitHub.
6. Open a Pull Request targeting `main`.
7. Link the related GitHub issue.
8. Request code review.
9. Address review feedback.
10. Merge the PR after receiving the required approval.
11. Delete the feature branch after merging.

This workflow keeps `main` stable while providing traceability between issues, commits, code reviews, and completed work.
