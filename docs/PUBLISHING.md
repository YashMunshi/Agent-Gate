# Publishing Agent Gate on GitHub

Suggested repository: `YashMunshi/agent-gate`.

## Option 1: GitHub website

1. Create a repository at https://github.com/new named `agent-gate`.
2. Choose Public if you want recruiters to see it.
3. If uploading files yourself, leave initialization options unchecked.
4. Extract the ZIP and open the `agent-gate` folder.
5. Use the repository's **upload an existing file** link. Upload the extracted
   contents, not the ZIP and not an extra wrapper folder. `app.py` and `README.md`
   should be at the repository root.
6. Commit the upload. Include `.gitignore` and `.github/workflows/tests.yml`;
   these hidden items may need separate selection or the Git method below.
7. Open Actions to check the test workflow. Set a concise repository description
   and pin the repository to your profile if appropriate.

If you want ChatGPT to upload the files using the connected GitHub account,
create the repository **with a README** so it has an initial commit, then
provide its URL in the chat. The available connector can write files to an
existing repository but does not expose repository creation.

## Option 2: Git from your terminal

Create an empty GitHub repository first, then run these commands inside the
extracted `agent-gate` folder:

```bash
git init -b main
git add .
git commit -m "Add Agent Gate security prototype"
git remote add origin https://github.com/YashMunshi/agent-gate.git
git push -u origin main
```

Authenticate using GitHub's supported login method when Git asks. Never paste
personal access tokens into source code or send them in chat.

Repository description: Scoped agent identities, exact-action approvals, and secure mock tool execution.
Suggested topics: python, sqlite, security-engineering, authorization, portfolio

The code will be public if you choose Public. This does not publish a working
website: the Python backend runs locally. No runtime database or account secrets
are included in the prepared ZIP.
