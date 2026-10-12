# aw-address-pr-issues: gather, triage, respond

Read-only until Ship, except the reply and resolve commands. Resolve `OWNER/REPO` and the PR number once.

## Gather

```sh
gh pr view --json number,title,url,headRefName,baseRefName,state,reviews,comments,statusCheckRollup
gh api --paginate repos/OWNER/REPO/pulls/PR/comments      # inline review comments
gh api --paginate repos/OWNER/REPO/issues/PR/comments     # conversation comments, bot reports
gh api --paginate repos/OWNER/REPO/pulls/PR/reviews       # APPROVED / CHANGES_REQUESTED / COMMENTED
gh pr checks PR
```

Resolved state is not in the REST payload:

```sh
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100){ nodes {
        id isResolved isOutdated
        comments(first:50){ nodes { databaseId author{login} body path line } }
      }}
    }
  }
}' -F owner=OWNER -F repo=REPO -F pr=PR
```

Failing checks: `gh run view <run-id> --log-failed` for the root cause, then decide `valid` (regression from this branch) or environmental. Dependabot, CodeQL, and other bot findings arrive as comments or checks; triage them like human comments.

## Triage: the complete-picture test

Per item, walk the whole thread and answer in order:

1. Still open? Resolved, answered, deferred, overruled, or fixed by a later commit: `already-addressed`.
2. Survives the sources? Check against `specs/**` + `proposal.md`, `docs/adr/`, and `rules/`. Contradiction or refuted assumption: `invalid` (record source and why).
3. Otherwise `valid`. Note a shared root cause so one fix closes several comments.

Fix-loop tells:

- Same finding re-raised after a "fixed" reply: the earlier fix was a symptom patch. Grep every caller.
- Two comments pulling opposite ways: at most one is `valid`.
- A bot re-flagging an ADR-backed decision: `invalid`; cite the ADR.

Table columns: `# | source | thread | class | reason | fix plan`.

## Respond

- `valid`: reply with the fixing commit SHA; resolve.
- `already-addressed`: reply linking the prior commit or reply; resolve.
- `invalid`: reply citing the ADR, spec requirement, or rule clause; leave open for the reviewer unless they agreed.

```sh
gh api repos/OWNER/REPO/pulls/PR/comments/COMMENT_ID/replies -f body="..."
gh pr comment PR --body "..."        # one summary instead of many replies
gh api graphql -f query='mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ thread { isResolved } } }' -F id=THREAD_ID
```

Never paste secrets or internal error text into PR comments.
