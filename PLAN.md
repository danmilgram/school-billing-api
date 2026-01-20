# School Billing API – Execution Plan

  ## Code Quality
- [ ] Add `ruff`
- [ ] Configure linting rules
- [ ] Format entire codebase
- [ ] (Optional) pre-commit hooks

## Caching & Performance
- [ ] Add Redis service
- [ ] Cache read-heavy endpoints:
  - School account statement
  - Student account statement
- [ ] Invalidate cache on invoice/payment changes

## Observability
- [ ] Add loggs
- [ ] Prometheus basic metrics

## Final Documentation
- [] Complete README with:
  - Architecture and design patterns
  - Setup instructions
  - Docker commands
  - API endpoint documentation with examples
  - Migration workflow
  - Test execution and coverage
  - Development workflow

# Double check
- Core bussiness rules
- Validations
- Manual tests
