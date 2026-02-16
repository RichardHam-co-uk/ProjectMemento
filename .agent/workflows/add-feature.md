---
description: How to add a new feature as an AI agent
---

1. **Research**: Check `ROADMAP.md` and existing issues to understand the feature requirements.
2. **Branch**: Create a new branch `ai/feat-<feature-name>` from `main`.
3. **Plan**: Create an implementation plan and share it with the user/human sponsor.
4. **Implement**: 
   - Add source code in `src/`.
   - Add tests in `tests/`.
   - Update documentation in `docs/` or `README.md`.
5. **Verify**:
   - Run `npm test` to ensure all tests pass.
   - Run `npm run lint` to ensure code style compliance.
6. **PR**: Open a Pull Request to `main`. Include a summary of changes and mention that it was AI-generated.
