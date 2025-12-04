# ReadTheDocs Setup Guide

This guide explains how to publish the same documentation to both ReadTheDocs URLs.

## Current Status

- **Submitted URL** (in your project submission): https://rahul1269227-transaction-ai.readthedocs.io
- **Current URL** (working): https://transaction-ai.readthedocs.io/en/latest/

## Goal

Make the documentation available at **both URLs** so your submission link works.

---

## Solution: Set Up Both ReadTheDocs Projects

### Option 1: Use the Same Project with Custom Domain

ReadTheDocs allows you to have both the default URL and a custom slug.

1. Go to your project settings on ReadTheDocs
2. Check if you can add `rahul1269227-transaction-ai` as an alias

### Option 2: Create Two Separate Projects (Recommended)

Since you can't resubmit, the safest approach is to have the repository published under both project names.

#### Step 1: Verify Existing Project

1. Go to https://readthedocs.org/dashboard/
2. Check if you have a project named `rahul1269227-transaction-ai`
3. If **YES** → Go to Step 2
4. If **NO** → Go to Step 3

#### Step 2: Connect Existing Project

If the project exists but isn't building:

1. Navigate to: https://readthedocs.org/projects/rahul1269227-transaction-ai/
2. Click **Admin** → **Integrations**
3. Add a **GitHub webhook** if not present
4. Go to **Builds** and click **Build Version: latest**

#### Step 3: Import as New Project

If the project doesn't exist:

1. Go to https://readthedocs.org/dashboard/
2. Click **Import a Project**
3. Select your GitHub repository: `Rahul1269227/transaction-ai`
4. **IMPORTANT:** Change the project name to `rahul1269227-transaction-ai` (the exact name from your submission)
5. Click **Next** and **Finish**
6. The build should start automatically

#### Step 4: Verify Configuration

Once the project is created:

1. Go to **Admin** → **Settings**
2. Verify:
   - **Name**: `rahul1269227-transaction-ai`
   - **Repository URL**: `https://github.com/Rahul1269227/transaction-ai`
   - **Default branch**: `main`

3. Go to **Admin** → **Advanced Settings**
4. Verify:
   - **Default version**: `latest`
   - **Documentation type**: `mkdocs`

#### Step 5: Trigger Build

1. Go to **Builds** tab
2. Click **Build Version: latest**
3. Wait for the build to complete (2-3 minutes)
4. Check build logs for any errors

#### Step 6: Verify Both URLs Work

Test both URLs:

```bash
# Test old URL (from submission)
curl -I https://rahul1269227-transaction-ai.readthedocs.io

# Test new URL
curl -I https://transaction-ai.readthedocs.io/en/latest/
```

Both should return `HTTP/2 200` status.

---

## Current MkDocs Configuration

Your `mkdocs.yml` is already configured correctly:

```yaml
site_url: https://rahul1269227-transaction-ai.readthedocs.io
```

This means when ReadTheDocs builds the project named `rahul1269227-transaction-ai`, it will automatically use this URL.

---

## Automatic Builds

To ensure both projects stay in sync:

### GitHub Webhook (Automatic)

ReadTheDocs should automatically set up webhooks when you import the project. Verify:

1. Go to GitHub: https://github.com/Rahul1269227/transaction-ai/settings/hooks
2. You should see webhook(s) pointing to `https://readthedocs.org/api/v2/webhook/...`
3. If missing, ReadTheDocs will add it when you import the project

### Manual Build Trigger

If automatic builds don't work:

1. Go to ReadTheDocs project: https://readthedocs.org/projects/rahul1269227-transaction-ai/builds/
2. Click **Build Version** button
3. Select **latest** and click **Build**

---

## Troubleshooting

### Build Fails

**Check build logs:**
1. Go to https://readthedocs.org/projects/rahul1269227-transaction-ai/builds/
2. Click on the failed build
3. Review the error log

**Common issues:**

1. **Missing `docs/requirements.txt`:**
   ```bash
   # Create docs/requirements.txt with:
   mkdocs-material>=9.0.0
   mkdocs-minify-plugin>=0.6.0
   ```

2. **Missing documentation files:**
   - Ensure all `.md` files referenced in `mkdocs.yml` exist in `docs/` folder

3. **Python version mismatch:**
   - `.readthedocs.yaml` specifies Python 3.11
   - Ensure your local MkDocs works with Python 3.11

### URL Not Working

**Wait for DNS propagation:**
- New projects may take 5-10 minutes for DNS to propagate

**Clear browser cache:**
```bash
# Hard refresh
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

**Check project status:**
```bash
curl -I https://rahul1269227-transaction-ai.readthedocs.io
```

Should return:
```
HTTP/2 200
```

---

## Maintaining Both Projects

### Option A: Keep Both Projects Separate

- Both projects build from the same GitHub repository
- Both automatically rebuild on new commits
- No extra maintenance needed

### Option B: Use One Project with Redirect

If you can modify the newer project (`transaction-ai`):

1. Go to https://readthedocs.org/projects/transaction-ai/
2. Admin → Settings → **Custom domains**
3. Try to add `rahul1269227-transaction-ai.readthedocs.io` as an alias

(Note: This may not be possible as it's a different project name)

---

## Recommended Approach

**Use Option 2, Step 3**: Import as a new project named `rahul1269227-transaction-ai`

This is the safest and cleanest solution:
✅ Works with your submitted URL
✅ No code changes needed
✅ Automatic builds from GitHub
✅ Independent of the other project

---

## Quick Checklist

- [ ] Log in to ReadTheDocs
- [ ] Check if `rahul1269227-transaction-ai` project exists
- [ ] If not, import repository with exact project name
- [ ] Verify `.readthedocs.yaml` and `mkdocs.yml` are in repository root
- [ ] Trigger build manually
- [ ] Wait for build to complete (check logs)
- [ ] Test URL: https://rahul1269227-transaction-ai.readthedocs.io
- [ ] Verify all pages load correctly

---

## Support

If you encounter issues:

1. **ReadTheDocs Documentation**: https://docs.readthedocs.io/
2. **MkDocs Documentation**: https://www.mkdocs.org/
3. **Build Logs**: Check for specific error messages

---

**Last Updated**: November 24, 2025
