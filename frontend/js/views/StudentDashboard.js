/**
 * StudentDashboard.js — Student dashboard (5 tabs inside AppShell).
 *
 * Tabs: Overview, Browse Drives, My Applications, History, Profile.
 * All data is loaded in parallel via Promise.all() on mount.
 * Uses the AppShell component for sidebar/topbar layout.
 * Role accent color: violet (set via data-role="student" in AppShell).
 */
const StudentDashboardView = {
  template: `
  <app-shell role="student" title="Student" :nav-items="tabs" v-model="activeTab">

    <!-- ===== OVERVIEW ===== -->
    <template v-if="activeTab === 'overview'">
      <div class="row g-3 mb-4">
        <div class="col-sm-6 col-lg-3" v-for="s in overviewStats" :key="s.label">
          <div class="stat-card">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <div class="stat-label">{{ s.label }}</div>
                <div class="stat-value" :style="s.color ? 'color:'+s.color : ''">{{ s.value }}</div>
              </div>
              <i :class="s.icon + ' stat-icon'"></i>
            </div>
          </div>
        </div>
      </div>

      <div class="pp-card mb-4" v-if="student">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div>
            <h5 class="fw-bold mb-1 font-display">{{ student.full_name }}</h5>
            <div class="text-muted mb-1"><i class="bi bi-card-text me-1"></i>{{ student.roll_number }}</div>
            <div class="text-muted mb-1"><i class="bi bi-diagram-3 me-1"></i>{{ student.branch }} · Year {{ student.year_of_study }}</div>
            <div class="text-muted"><i class="bi bi-star me-1"></i>CGPA: <strong>{{ student.cgpa }}</strong></div>
          </div>
          <div>
            <span v-if="student.resume_path" class="pill pill-ok"><i class="bi bi-file-earmark-pdf"></i> Resume uploaded</span>
            <span v-else class="pill pill-warn"><i class="bi bi-exclamation-triangle"></i> No resume</span>
          </div>
        </div>
      </div>

      <div class="pp-card">
        <div class="pp-card-head"><h6>Recent Applications</h6></div>
        <div v-if="!dashboard.my_applications || dashboard.my_applications.length === 0" class="empty-state">
          <i class="bi bi-inbox"></i>No applications yet — browse drives to get started.
        </div>
        <div v-for="a in dashboard.my_applications" :key="a.id"
          class="d-flex justify-content-between align-items-center py-2" style="border-bottom:1px solid var(--line);">
          <div>
            <div class="fw-semibold">{{ a.job_title }}</div>
            <div class="text-muted small">{{ a.company_name }}</div>
          </div>
          <span class="pill" :class="'pill-'+a.status">{{ a.status }}</span>
        </div>
      </div>
    </template>

    <!-- ===== BROWSE DRIVES ===== -->
    <template v-if="activeTab === 'drives'">
      <div class="d-flex gap-2 mb-3 flex-wrap">
        <input v-model="driveSearch" type="text" class="form-control" style="max-width:340px;"
          placeholder="Search by job title or company…" />
        <div class="form-check form-switch d-flex align-items-center ms-2">
          <input class="form-check-input me-2" type="checkbox" v-model="eligibleOnly" id="eligToggle" />
          <label class="form-check-label text-nowrap" for="eligToggle">Eligible only</label>
        </div>
      </div>

      <div v-if="filteredDrives.length === 0" class="empty-state">
        <i class="bi bi-briefcase"></i>No drives match your criteria.
      </div>

      <div v-for="d in filteredDrives" :key="d.id" class="pp-card mb-3"
        :style="d.is_eligible ? '' : 'opacity:.7'">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div>
            <h6 class="fw-bold mb-1">
              {{ d.job_title }}
              <span v-if="!d.is_eligible" class="pill pill-neutral ms-1">Not eligible</span>
            </h6>
            <div class="text-muted small mb-2">
              <i class="bi bi-building me-1"></i>{{ d.company_name }}
              &nbsp;·&nbsp;<i class="bi bi-currency-rupee"></i>{{ d.package_lpa }} LPA
              &nbsp;·&nbsp;<i class="bi bi-briefcase me-1"></i>{{ d.job_type }}
            </div>
            <div class="d-flex flex-wrap gap-1 mb-2">
              <span v-for="b in d.eligible_branches" :key="b" class="pill pill-neutral">{{ b }}</span>
            </div>
            <div class="text-muted small">
              <i class="bi bi-star me-1"></i>Min CGPA: {{ d.min_cgpa }}
              &nbsp;·&nbsp;<i class="bi bi-calendar me-1"></i>Deadline: {{ d.application_deadline }}
            </div>
          </div>
          <div class="text-end">
            <div v-if="d.already_applied" class="text-center">
              <span class="pill" :class="'pill-'+d.application_status">{{ d.application_status }}</span>
              <div class="text-muted small mt-1">Already applied</div>
            </div>
            <button v-else-if="d.is_eligible" class="btn btn-accent btn-sm" @click="applyDrive(d.id)">
              <i class="bi bi-send me-1"></i>Apply now
            </button>
            <button v-else class="btn btn-outline-secondary btn-sm" disabled>Not eligible</button>
          </div>
        </div>
      </div>
    </template>

    <!-- ===== MY APPLICATIONS ===== -->
    <template v-if="activeTab === 'applications'">
      <div class="section-head">
        <h5>My Applications</h5>
        <button class="btn btn-outline-primary btn-sm" @click="exportCSV">
          <i class="bi bi-download me-1"></i>Export CSV
        </button>
      </div>
      <div v-if="exportMsg" class="alert alert-info py-2">{{ exportMsg }}</div>

      <div v-if="applications.length === 0" class="empty-state">
        <i class="bi bi-file-earmark-text"></i>No applications yet.
      </div>

      <div v-for="a in applications" :key="a.id" class="pp-card mb-3">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div class="flex-grow-1">
            <h6 class="fw-bold mb-1">{{ a.job_title }}</h6>
            <div class="text-muted small">
              <i class="bi bi-building me-1"></i>{{ a.company_name }}
              &nbsp;·&nbsp;<i class="bi bi-currency-rupee"></i>{{ a.package_lpa }} LPA
            </div>
            <div class="text-muted small mt-1">
              <i class="bi bi-calendar me-1"></i>Applied: {{ a.application_date }}
            </div>

            <div v-if="a.interview" class="mt-2 p-2 rounded" style="background:var(--accent-050);border-left:3px solid var(--accent);">
              <div class="fw-semibold small mb-1">
                <i class="bi bi-camera-video me-1" style="color:var(--accent)"></i>Interview Scheduled
              </div>
              <div class="small text-muted"><i class="bi bi-clock me-1"></i>{{ new Date(a.interview.scheduled_at).toLocaleString() }}</div>
              <div class="small text-muted">
                <i class="bi bi-geo-alt me-1"></i>{{ a.interview.mode }}
                <span v-if="a.interview.location"> — {{ a.interview.location }}</span>
              </div>
              <div v-if="a.interview.notes" class="small text-muted"><i class="bi bi-sticky me-1"></i>{{ a.interview.notes }}</div>
              <div class="mt-1"><span class="pill" :class="'pill-'+a.interview.result">Result: {{ a.interview.result }}</span></div>
            </div>

            <div v-else-if="a.status === 'shortlisted'" class="mt-2">
              <span class="pill pill-warn"><i class="bi bi-hourglass-split me-1"></i>Interview not scheduled yet</span>
            </div>
          </div>
          <span class="pill" :class="'pill-'+a.status" style="font-size:.82rem;">{{ a.status }}</span>
        </div>
      </div>
    </template>

    <!-- ===== HISTORY ===== -->
    <template v-if="activeTab === 'history'">
      <div class="section-head"><h5>Placement History</h5></div>

      <div v-if="history.length === 0" class="empty-state">
        <i class="bi bi-clock-history"></i>No history yet.
      </div>

      <div v-for="h in history" :key="h.id" class="pp-card mb-3">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div class="flex-grow-1">
            <h6 class="fw-bold mb-1">{{ h.job_title }}</h6>
            <div class="text-muted small">
              <i class="bi bi-building me-1"></i>{{ h.company_name }}
              &nbsp;·&nbsp;<i class="bi bi-briefcase me-1"></i>{{ h.job_type }}
              &nbsp;·&nbsp;<i class="bi bi-currency-rupee"></i>{{ h.package_lpa }} LPA
            </div>
            <div class="text-muted small mt-1"><i class="bi bi-calendar me-1"></i>Applied: {{ h.application_date }}</div>

            <div v-if="h.interview" class="mt-2 p-2 rounded" style="background:var(--accent-050);border-left:3px solid var(--accent);">
              <div class="fw-semibold small mb-1"><i class="bi bi-camera-video me-1" style="color:var(--accent)"></i>Interview Details</div>
              <div class="small text-muted">
                <i class="bi bi-clock me-1"></i>{{ new Date(h.interview.scheduled_at).toLocaleString() }}
                &nbsp;·&nbsp;<i class="bi bi-geo-alt me-1"></i>{{ h.interview.mode }}
                <span v-if="h.interview.location"> — {{ h.interview.location }}</span>
              </div>
              <div class="mt-1"><span class="pill" :class="'pill-'+h.interview.result">Interview: {{ h.interview.result }}</span></div>
            </div>
          </div>
          <span class="pill" :class="'pill-'+h.status" style="font-size:.82rem;">{{ h.status }}</span>
        </div>
      </div>
    </template>

    <!-- ===== PROFILE ===== -->
    <template v-if="activeTab === 'profile'">
      <div class="row g-4">
        <div class="col-md-6">
          <div class="pp-card">
            <div class="pp-card-head"><h6>Edit Profile</h6></div>
            <div v-if="profileSuccess" class="alert alert-success py-2">{{ profileSuccess }}</div>
            <div class="mb-3">
              <label class="form-label">Full name</label>
              <input v-model="profileForm.full_name" type="text" class="form-control" />
            </div>
            <div class="mb-3">
              <label class="form-label">Phone</label>
              <input v-model="profileForm.phone" type="text" class="form-control" />
            </div>
            <div class="mb-3">
              <label class="form-label">Branch</label>
              <select v-model="profileForm.branch" class="form-select">
                <option>CS</option><option>IT</option><option>ECE</option>
                <option>EEE</option><option>ME</option><option>CE</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">CGPA</label>
              <input v-model="profileForm.cgpa" type="number" step="0.1" class="form-control" />
            </div>
            <div class="mb-3">
              <label class="form-label">Year of study</label>
              <select v-model="profileForm.year_of_study" class="form-select">
                <option value="1">1st Year</option><option value="2">2nd Year</option>
                <option value="3">3rd Year</option><option value="4">4th Year</option>
              </select>
            </div>
            <button class="btn btn-accent" @click="updateProfile"><i class="bi bi-save me-1"></i>Save changes</button>
          </div>
        </div>
        <div class="col-md-6">
          <div class="pp-card">
            <div class="pp-card-head"><h6>Upload Resume</h6></div>
            <div v-if="resumeSuccess" class="alert alert-success py-2">{{ resumeSuccess }}</div>
            <div v-if="resumeError" class="alert alert-danger py-2">{{ resumeError }}</div>
            <div v-if="student && student.resume_path" class="alert alert-info py-2 mb-3">
              <i class="bi bi-file-earmark-pdf me-2"></i>Current: {{ student.resume_path }}
            </div>
            <div class="mb-3">
              <label class="form-label">Select PDF file</label>
              <input type="file" accept=".pdf" class="form-control" @change="onResumeSelect" />
            </div>
            <button class="btn btn-accent" @click="uploadResume" :disabled="!resumeFile">
              <i class="bi bi-upload me-1"></i>Upload resume
            </button>
          </div>
        </div>
      </div>
    </template>

  </app-shell>
  `,
  data() {
    return {
      activeTab: 'overview',
      tabs: [
        { key: 'overview', label: 'Overview', icon: 'bi bi-grid' },
        { key: 'drives', label: 'Browse Drives', icon: 'bi bi-briefcase' },
        { key: 'applications', label: 'My Applications', icon: 'bi bi-file-earmark-text' },
        { key: 'history', label: 'History', icon: 'bi bi-clock-history' },
        { key: 'profile', label: 'Profile', icon: 'bi bi-person-gear' },
      ],
      dashboard: {},
      student: null,
      drives: [],
      applications: [],
      history: [],
      driveSearch: '',
      eligibleOnly: false,
      profileForm: {},
      profileSuccess: '',
      resumeFile: null,
      resumeSuccess: '',
      resumeError: '',
      exportMsg: '',
    }
  },
  computed: {
    eligibleDrives() {
      return this.drives.filter(d => d.is_eligible && !d.already_applied)
    },
    filteredDrives() {
      let result = this.drives
      if (this.eligibleOnly) result = result.filter(d => d.is_eligible)
      if (this.driveSearch) {
        const q = this.driveSearch.toLowerCase()
        result = result.filter(d =>
          d.job_title.toLowerCase().includes(q) ||
          d.company_name.toLowerCase().includes(q)
        )
      }
      return result
    },
    overviewStats() {
      return [
        { label: 'Available Drives', value: this.eligibleDrives.length, icon: 'bi bi-briefcase-fill', color: 'var(--accent)' },
        { label: 'Applied', value: this.dashboard.total_applied || 0, icon: 'bi bi-send-fill', color: '' },
        { label: 'Shortlisted', value: this.dashboard.shortlisted || 0, icon: 'bi bi-bookmark-star-fill', color: 'var(--warn)' },
        { label: 'Selected', value: this.dashboard.selected || 0, icon: 'bi bi-trophy-fill', color: 'var(--ok)' },
      ]
    },
  },
  async mounted() { await this.loadAll() },
  methods: {
    async loadAll() {
      const [dash, drives, apps, hist, profile] = await Promise.all([
        axios.get('/api/student/dashboard'),
        axios.get('/api/student/drives'),
        axios.get('/api/student/applications'),
        axios.get('/api/student/history'),
        axios.get('/api/student/profile'),
      ])
      this.dashboard = dash.data
      this.student = dash.data.student
      this.drives = drives.data
      this.applications = apps.data
      this.history = hist.data
      this.profileForm = { ...profile.data }
    },
    async applyDrive(driveId) {
      try {
        await axios.post('/api/student/drives/' + driveId + '/apply')
        this.$toast('Application submitted!', 'ok')
        await this.loadAll()
      } catch (err) {
        this.$toast(err.response?.data?.error || 'Failed to apply', 'err')
      }
    },
    async updateProfile() {
      await axios.put('/api/student/profile', this.profileForm)
      this.profileSuccess = 'Profile updated!'
      setTimeout(() => this.profileSuccess = '', 3000)
      await this.loadAll()
    },
    onResumeSelect(e) { this.resumeFile = e.target.files[0] },
    async uploadResume() {
      this.resumeError = ''
      this.resumeSuccess = ''
      if (!this.resumeFile) return
      const formData = new FormData()
      formData.append('resume', this.resumeFile)
      try {
        await axios.post('/api/student/profile/resume', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.resumeSuccess = 'Resume uploaded!'
        await this.loadAll()
      } catch (err) {
        this.resumeError = err.response?.data?.error || 'Upload failed'
      }
    },
    async exportCSV() {
      try {
        this.exportMsg = 'Starting export…'
        const res = await axios.post('/api/student/export/csv')
        const taskId = res.data.task_id
        this.exportMsg = 'Export in progress…'
        const poll = setInterval(async () => {
          try {
            const status = await axios.get('/api/student/export/status/' + taskId)
            if (status.data.status === 'done') {
              clearInterval(poll)
              this.exportMsg = 'Export complete — downloading…'
              window.open('/api/student/export/download/' + taskId)
            } else if (status.data.status === 'failed') {
              clearInterval(poll)
              this.exportMsg = 'Export failed. Please try again.'
            }
          } catch (e) {
            clearInterval(poll)
            this.exportMsg = 'Could not check export status.'
          }
        }, 2000)
      } catch (err) {
        this.exportMsg = 'Export failed. Make sure Celery is running.'
      }
    },
  },
}
