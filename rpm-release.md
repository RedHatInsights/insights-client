# Releasing The Insights Client RPM

## Prerequisites
All the stuff you need to get started. This guide assumes you're using a RHEL 8 or Fedora workstation.

### Red Hat Kerberos Auth

Refer to **Kerberos Setup** in [this document](https://source.redhat.com/groups/public/segteam/segteam_wiki/building_from_git_using_rhpkg) to set up Kerberos auth in your terminal.

### Required Packages
You will need these packages installed, which should be available in your base repos.
```
sudo yum install -y automake autoconf wget git
```

You will also need the rhpkg tools, which are available in repos provided on download.devel.redhat.com.

#### RHEL 8
```
sudo wget -P /etc/yum.repos.d/ http://download.devel.redhat.com/rel-eng/RCMTOOLS/rcm-tools-rhel-8-baseos.repo
sudo dnf install -y rhpkg brewkoji
```

#### Fedora
```
sudo wget -P /etc/yum.repos.d/ http://download.devel.redhat.com/rel-eng/RCMTOOLS/rcm-tools-fedora.repo
sudo dnf install -y rhpkg brewkoji
```

## 1. Creating Source Tarball Release
To create the insights-client source tarball, clone the repository and run the following command:
```
./autogen.sh; make dist
```

This will automatically download the latest `insights-core` egg, and create a tar.gz archive suitable for creating an RPM.

The generated tar.gz should also be uploaded to Github as a release.

To tag for a release, use the current value of the VERSION file and tag the current commit. Then push tags to origin (Gitlab).
```
git tag $(cat VERSION)
git push origin master --tags
```
You can now draft a release on Github with this tag. Attach the generated tar.gz to the release.

After pushing the tags, increment the VERSION file as needed (usually, incrementing the release by 1). Then commit the new VERSION.
```
git checkout -b release-bump
awk -F . '{printf("%d.%d.%d\n", $1, $2, $3+1) > "VERSION";}' VERSION
git add VERSION; git commit -m "post-release version bump"; git push origin release-bump
```
Open a new pull request on Gitlab to commit the new VERSION.

## 2. Bugzilla Approvals
For Y-stream builds in active development (ungated branch on dist-git), this step can be skipped.

Otherwise, in order to push commits to dist-git, one or more approved Bugzillas are required.

For example, if doing a Z-stream release to RHEL 8.4, a Bugzilla for the issue being fixed in this build, opened against RHEL 8.4, is needed.

The Bugzilla must be in the MODIFIED state.

The following acks are required, set by the developer (you), QA contact, and the RHEL PMs:
- devel_ack
- qa_ack
- zstream
- rhel-x.y.z (where x.y are the major/minor versions of RHEL for this BZ)
- release

Once the Bugzilla(s) have the proper acks, you can proceed to committing the code to dist-git.

**Note:** If a Bugzilla needs to be fixed in multiple versions of RHEL (e.g. the same fix goes into RHEL 7 and 8), the original BZ must be cloned and have the same set of acks applied.

## 3. Pushing to Brew

Clone the insights-client from dist-git using rhpkg.

```
rhpkg clone insights-client
cd insights-client
```
This will create a new directory `insights-client` with a git repo inside pointing to https://pkgs.devel.redhat.com/cgit/rpms/insights-client.

Enter the directory and checkout the release branch for which you want to build. For this example we'll assume a release for RHEL 8.

```
git checkout rhel-8.4.0
```
Add the insights-client-X.Y.Z.tar.gz you created in Step 1 as a new source.
```
rhpkg new-sources /path/to/insights-client-X.Y.Z.tar.gz
```
Update the specfile with the new NVR, changelog update, and any other necessary changes.
```
vim insights-client.spec
```
Add the specfile to the staged files for commit. The `sources` file should already be staged.
```
git add insights-client.spec
```
Commit the changes. In the commit message, include the resolved BZs from Step 2 with the format `Resolves: RHBZ#1234567, RHBZ#1234568`. See previous commits in the commit log for examples.
```
git commit
```
Push the changes.
```
rhpkg push
```
If any commit hooks prevent the push, double check your BZ acks and commit formatting. The commit hook message may have more details.

Do a scratch build to confirm that the build completes successfully.
```
rhpkg scratch-build
```

If all looks good, do the build.

**NOTE:** If building for a Z-stream release, you will need to explicitly set the `--target` option.
```
rhpkg build --target rhel-8.4.0-z-candidate
```

Otherwise, just do the command alone.
```
rhpkg build
```
The messaging while the build is running will link you to a Brew task. This task will also link you to the built RPMs when finished, so you can find the build ID later.

## 4. Errata Process
Go to https://errata.devel.redhat.com and under "**Tasks**" choose "**Create New Advisory**."

Choose "**Manual Create**."

Fill out the form with the release version, topic, resolved BZs, etc.

Add the Brew build you created in Step 3 by its ID. You can get this either from the builds linked from the build task in Brew, or search for the package in Brew and find the version you built. The ID will be in the URL.

RPMDiff will run. Waive or resolve any issues that come up.

Covscan will run. Waive or resolve any issues that come up.

If all is well, click **Move to QA** and let god sort em out.