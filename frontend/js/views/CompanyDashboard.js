/**
 * CompanyDashboard.js — Company dashboard (4 tabs inside AppShell).
 *
 * Tabs: Overview, My Drives, Applicants, Profile.
 * Includes a modal for scheduling/editing interviews.
 * Uses the AppShell component for sidebar/topbar layout.
 * Role accent color: emerald (set via data-role="company" in AppShell).
 */
const CompanyDashboardView = {
  template: `
  <app-shell role="company" title="Company" :nav-items="tabs" v-model="activeTab">

    <!-- Approval banners -->
    <div v-if="company && company.approval_status === 'pending'" class="alert alert-warning py-2 mb-3">
      <i class="bi bi-hourglass-split me-2"></i>Your company is pending admin approval. You cannot create drives yet.
    </div>
    <div v-if="company && company.approval_status === 'rejected'" class="alert alert-danger py-2 mb-3">
      <i class="bi bi-x-circle me-2"></i>Your registration was rejected. Please contact admin.
    </div>

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

      <div class="pp-card" v-if="company">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div>
            <h5 class="fw-bold mb-1 font-display">{{ company.company_name }}</h5>
            <div class="text-muted mb-1"><i class="bi bi-person me-1"></i>{{ company.hr_name }}</div>
            <div class="text-muted mb-1"><i class="bi bi-envelope me-1"></i>{{ company.hr_email }}</div>
            <div class="text-muted mb-1"><i class="bi bi-globe me-1"></i>{{ company.website }}</div>
            <div class="text-muted"><i class="bi bi-briefcase me-1"></i>{{ company.industry }}</div>
          </div>
          <span class="pill" :class="'pill-'+company.approval_status">{{ company.approval_status }}</span>
        </div>
      </div>
    </template>

    <!-- ===== DRIVES ===== -->
    <template v-if="activeTab === 'drives'">
      <div class="section-head">
        <h5>My Placement Drives</h5>
        <button class="btn btn-accent btn-sm"
          :disabled="company && company.approval_status !== 'approved'"
          @click="showCreateDrive = true">
          <i class="bi bi-plus-circle me-1"></i>Create drive
        </button>
      </div>

      <!-- Create drive form -->
      <div v-if="showCreateDrive" class="pp-card mb-4">
        <div class="pp-card-head"><h6>New Drive</h6></div>
        <div v-if="driveError" class="alert alert-danger py-2">{{ driveError }}</div>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Job title</label>
            <input v-model="newDrive.job_title" type="text" class="form-control" />
          </div>
          <div class="col-md-3">
            <label class="form-label">Package (LPA)</label>
            <input v-model="newDrive.package_lpa" type="number" class="form-control" />
          </div>
          <div class="col-md-3">
            <label class="form-label">Job type</label>
            <select v-model="newDrive.job_type" class="form-select">
              <option>Full-time</option><option>Internship</option><option>Contract</option>
            </select>
          </div>
          <div class="col-12">
            <label class="form-label">Job description</label>
            <textarea v-model="newDrive.job_description" class="form-control" rows="3"></textarea>
          </div>
          <div class="col-md-4">
            <label class="form-label">Eligible branches</label>
            <div class="d-flex flex-wrap gap-2">
              <div v-for="b in branchOptions" :key="b" class="form-check">
                <input class="form-check-input" type="checkbox" :value="b" v-model="newDrive.eligible_branches" />
                <label class="form-check-label">{{ b }}</label>
              </div>
            </div>
          </div>
          <div class="col-md-4">
            <label class="form-label">Min CGPA</label>
            <input v-model="newDrive.min_cgpa" type="number" step="0.1" min="0" max="10" class="form-control" />
          </div>
          <div class="col-md-4">
            <label class="form-label">Eligible year</label>
            <select v-model="newDrive.eligible_year" class="form-select">
              <option value="1">1st Year</option><option value="2">2nd Year</option>
              <option value="3">3rd Year</option><option value="4">4th Year</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Application deadline</label>
            <input v-model="newDrive.application_deadline" type="date" class="form-control" />
          </div>
        </div>
        <div class="d-flex gap-2 mt-3">
          <button class="btn btn-accent" @click="createDrive"><i class="bi bi-send me-1"></i>Submit for approval</button>
          <button class="btn btn-outline-secondary" @click="showCreateDrive = false">Cancel</button>
        </div>
      </div>

      <div v-if="drives.length === 0 && !showCreateDrive" class="empty-state">
        <i class="bi bi-briefcase"></i>No drives created yet.
      </div>

      <div v-for="d in drives" :key="d.id" class="pp-card mb-3">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div>
            <h6 class="fw-bold mb-1">{{ d.job_title }}</h6>
            <div class="text-muted small">
              <i class="bi bi-calendar me-1"></i>Deadline: {{ d.application_deadline }}
              &nbsp;·&nbsp;<i class="bi bi-currency-rupee"></i>{{ d.package_lpa }} LPA
              &nbsp;·&nbsp;<i class="bi bi-people me-1"></i>{{ d.total_applicants }} applicants
            </div>
          </div>
          <div class="d-flex align-items-center gap-2 flex-wrap">
            <span class="pill" :class="'pill-'+d.status">{{ d.status }}</span>
            <button class="btn btn-outline-primary btn-sm" @click="viewApplications(d.id)">
              <i class="bi bi-eye me-1"></i>Applicants
            </button>
            <button v-if="d.status === 'approved'" class="btn btn-outline-secondary btn-sm" @click="closeDrive(d.id)">
              <i class="bi bi-check-circle me-1"></i>Complete
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- ===== APPLICANTS ===== -->
    <template v-if="activeTab === 'applicants'">
      <div class="section-head">
        <h5>Applicants <span v-if="selectedDriveTitle" class="text-muted fw-normal">— {{ selectedDriveTitle }}</span></h5>
      </div>

      <div v-if="!selectedDriveId" class="empty-state">
        <i class="bi bi-people"></i>Go to Drives and click "Applicants" to see candidates.
      </div>

      <div v-else class="pp-card" style="overflow-x:auto">
        <table class="pp-table">
          <thead>
            <tr>
              <th>Name</th><th>Roll No</th><th>Branch</th><th>CGPA</th>
              <th>Resume</th><th>Interview</th><th>Status</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in applicants" :key="a.id">
              <td class="fw-semibold">{{ a.student_name }}</td>
              <td>{{ a.roll_number }}</td>
              <td>{{ a.branch }}</td>
              <td class="tnum">{{ a.cgpa }}</td>
              <td>
                <a v-if="a.resume_path" :href="'/api/student/resume/'+a.resume_path" target="_blank"
                  class="btn btn-sm btn-outline-primary">
                  <i class="bi bi-file-earmark-pdf me-1"></i>View
                </a>
                <span v-else class="text-muted small">None</span>
              </td>
              <td>
                <div v-if="a.interview">
                  <div class="small text-muted">{{ new Date(a.interview.scheduled_at).toLocaleDateString() }}</div>
                  <span class="pill" :class="'pill-'+a.interview.result">{{ a.interview.result }}</span>
                </div>
                <span v-else class="text-muted small">Not scheduled</span>
              </td>
              <td><span class="pill" :class="'pill-'+a.status">{{ a.status }}</span></td>
              <td>
                <div class="d-flex gap-1 flex-wrap">
                  <select class="form-select form-select-sm" style="width:auto;" :value="a.status"
                    @change="updateStatus(a.id, $event.target.value)">
                    <option value="applied">Applied</option><option value="shortlisted">Shortlisted</option>
                    <option value="selected">Selected</option><option value="rejected">Rejected</option>
                  </select>
                  <button class="btn btn-accent btn-sm" @click="openInterviewModal(a)">
                    <i class="bi bi-calendar-plus me-1"></i>{{ a.interview ? 'Edit' : 'Schedule' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ===== PROFILE ===== -->
    <template v-if="activeTab === 'profile'">
      <div class="pp-card" style="max-width:600px;">
        <div class="pp-card-head"><h6>Edit Company Profile</h6></div>
        <div v-if="profileSuccess" class="alert alert-success py-2">{{ profileSuccess }}</div>
        <div class="mb-3"><label class="form-label">HR name</label><input v-model="profileForm.hr_name" class="form-control" /></div>
        <div class="mb-3"><label class="form-label">HR email</label><input v-model="profileForm.hr_email" type="email" class="form-control" /></div>
        <div class="mb-3"><label class="form-label">Website</label><input v-model="profileForm.website" class="form-control" /></div>
        <div class="mb-3"><label class="form-label">Industry</label><input v-model="profileForm.industry" class="form-control" /></div>
        <div class="mb-3"><label class="form-label">Description</label><textarea v-model="profileForm.description" class="form-control" rows="3"></textarea></div>
        <button class="btn btn-accent" @click="updateProfile"><i class="bi bi-save me-1"></i>Save changes</button>
      </div>
    </template>

    <!-- ===== INTERVIEW MODAL ===== -->
    <div v-if="showInterviewModal" class="pp-modal-back" @click.self="showInterviewModal = false">
      <div class="pp-modal">
        <div class="pp-modal-head">
          <h5><i class="bi bi-calendar-plus me-2"></i>{{ interviewForm.existing ? 'Edit Interview' : 'Schedule Interview' }}</h5>
          <button class="btn-close btn-close-white" @click="showInterviewModal = false"></button>
        </div>
        <div class="pp-modal-body">
          <div class="mb-3 p-2 rounded" style="background:var(--surface-2);">
            <strong>{{ interviewForm.student_name }}</strong>
            <div class="text-muted small">{{ interviewForm.drive_title }}</div>
          </div>
          <div class="mb-3">
            <label class="form-label">Date &amp; time</label>
            <input v-model="interviewForm.scheduled_at" type="datetime-local" class="form-control" />
          </div>
          <div class="mb-3">
            <label class="form-label">Mode</label>
            <select v-model="interviewForm.mode" class="form-select">
              <option>Online</option><option>In-Person</option><option>Phone</option>
            </select>
          </div>
          <div class="mb-3">
            <label class="form-label">Location / Link</label>
            <input v-model="interviewForm.location" class="form-control" placeholder="Google Meet link or office address" />
          </div>
          <div class="mb-3">
            <label class="form-label">Notes</label>
            <textarea v-model="interviewForm.notes" class="form-control" rows="2" placeholder="Instructions for the candidate…"></textarea>
          </div>
          <div v-if="interviewForm.existing" class="mb-3">
            <label class="form-label">Interview result</label>
            <select v-model="interviewForm.result" class="form-select">
              <option value="pending">Pending</option>
              <option value="passed">Passed → Selected</option>
              <option value="failed">Failed → Rejected</option>
            </select>
            <div class="form-text">Passed marks the student as Selected. Failed marks as Rejected.</div>
          </div>
        </div>
        <div class="pp-modal-foot">
          <button class="btn btn-accent" @click="saveInterview">
            <i class="bi bi-check-circle me-1"></i>{{ interviewForm.existing ? 'Update' : 'Schedule' }}
          </button>
          <button class="btn btn-outline-secondary" @click="showInterviewModal = false">Cancel</button>
        </div>
      </div>
    </div>

  </app-shell>
  `,
  data() {
    return {
      activeTab: 'overview',
      tabs: [
        { key: 'overview', label: 'Overview', icon: 'bi bi-grid' },
        { key: 'drives', label: 'My Drives', icon: 'bi bi-briefcase' },
        { key: 'applicants', label: 'Applicants', icon: 'bi bi-people' },
        { key: 'profile', label: 'Profile', icon: 'bi bi-person-gear' },
      ],
      dashboard: {},
      company: null,
      drives: [],
      applicants: [],
      selectedDriveId: null,
      selectedDriveTitle: '',
      showCreateDrive: false,
      driveError: '',
      profileSuccess: '',
      profileForm: {},
      newDrive: {
        job_title: '', job_description: '', eligible_branches: [],
        min_cgpa: 6.0, eligible_year: 4,
        application_deadline: '', package_lpa: 0, job_type: 'Full-time'
      },
      branchOptions: ['CS', 'IT', 'ECE', 'EEE', 'ME', 'CE'],
      showInterviewModal: false,
      interviewForm: {
        application_id: null, student_name: '', drive_title: '',
        scheduled_at: '', mode: 'Online', location: '', notes: '',
        result: 'pending', existing: false
      },
    }
  },
  computed: {
    totalApplicants() { return this.drives.reduce((s, d) => s + (d.total_applicants || 0), 0) },
    totalShortlisted() { return this.drives.reduce((s, d) => s + (d.shortlisted || 0), 0) },
    totalSelected() { return this.drives.reduce((s, d) => s + (d.selected || 0), 0) },
    overviewStats() {
      return [
        { label: 'Total Drives', value: this.dashboard.total_drives || 0, icon: 'bi bi-briefcase-fill', color: '' },
        { label: 'Total Applicants', value: this.totalApplicants, icon: 'bi bi-people-fill', color: 'var(--accent)' },
        { label: 'Shortlisted', value: this.totalShortlisted, icon: 'bi bi-bookmark-star-fill', color: 'var(--warn)' },
        { label: 'Selected', value: this.totalSelected, icon: 'bi bi-trophy-fill', color: 'var(--ok)' },
      ]
    },
  },
  async mounted() {
    await this.loadDashboard()
    await this.loadProfile()
  },
  methods: {
    async loadDashboard() {
      const res = await axios.get('/api/company/dashboard')
      this.dashboard = res.data
      this.company = res.data.company
      this.drives = res.data.drives
    },
    async loadProfile() {
      const res = await axios.get('/api/company/profile')
      this.profileForm = { ...res.data }
    },
    async createDrive() {
      this.driveError = ''
      if (!this.newDrive.job_title?.trim()) { this.driveError = 'Job title is required'; return }
      if (!this.newDrive.job_description?.trim()) { this.driveError = 'Job description is required'; return }
      if (this.newDrive.eligible_branches.length === 0) { this.driveError = 'Select at least one branch'; return }
      if (!this.newDrive.min_cgpa || this.newDrive.min_cgpa < 0 || this.newDrive.min_cgpa > 10) { this.driveError = 'Min CGPA must be 0-10'; return }
      if (!this.newDrive.application_deadline) { this.driveError = 'Deadline is required'; return }
      if (new Date(this.newDrive.application_deadline) < new Date()) { this.driveError = 'Deadline must be a future date'; return }
      try {
        await axios.post('/api/company/drives', this.newDrive)
        this.showCreateDrive = false
        this.newDrive = { job_title:'', job_description:'', eligible_branches:[], min_cgpa:6.0, eligible_year:4, application_deadline:'', package_lpa:0, job_type:'Full-time' }
        this.$toast('Drive submitted for approval', 'ok')
        await this.loadDashboard()
      } catch (err) {
        this.driveError = err.response?.data?.error || 'Failed to create drive'
      }
    },
    async viewApplications(driveId) {
      this.selectedDriveId = driveId
      const drive = this.drives.find(d => d.id === driveId)
      this.selectedDriveTitle = drive?.job_title || ''
      const res = await axios.get('/api/company/drives/' + driveId + '/applications')
      this.applicants = res.data
      this.activeTab = 'applicants'
    },
    async updateStatus(appId, status) {
      await axios.patch('/api/company/applications/' + appId + '/status', { status })
      await this.viewApplications(this.selectedDriveId)
    },
    async closeDrive(driveId) {
      if (!confirm('Mark this drive as complete? This cannot be undone.')) return
      try {
        await axios.patch('/api/company/drives/' + driveId + '/close')
        this.$toast('Drive marked as complete', 'ok')
        await this.loadDashboard()
      } catch (err) {
        this.$toast(err.response?.data?.error || 'Failed to close drive', 'err')
      }
    },
    openInterviewModal(applicant) {
      this.interviewForm = {
        application_id: applicant.id,
        student_name: applicant.student_name,
        drive_title: this.selectedDriveTitle,
        scheduled_at: applicant.interview ? applicant.interview.scheduled_at.slice(0, 16) : '',
        mode: applicant.interview?.mode || 'Online',
        location: applicant.interview?.location || '',
        notes: applicant.interview?.notes || '',
        result: applicant.interview?.result || 'pending',
        existing: !!applicant.interview,
      }
      this.showInterviewModal = true
    },
    async saveInterview() {
      if (!this.interviewForm.scheduled_at) {
        this.$toast('Select a date and time', 'err'); return
      }
      try {
        const scheduledAt = new Date(this.interviewForm.scheduled_at).toISOString()
        await axios.post('/api/company/applications/' + this.interviewForm.application_id + '/interview', {
          scheduled_at: scheduledAt, mode: this.interviewForm.mode,
          location: this.interviewForm.location, notes: this.interviewForm.notes,
        })
        if (this.interviewForm.existing && this.interviewForm.result !== 'pending') {
          await axios.patch('/api/company/applications/' + this.interviewForm.application_id + '/interview/result', {
            result: this.interviewForm.result
          })
        }
        this.showInterviewModal = false
        this.$toast('Interview saved', 'ok')
        await this.viewApplications(this.selectedDriveId)
      } catch (err) {
        this.$toast(err.response?.data?.error || 'Failed to save interview', 'err')
      }
    },
    async updateProfile() {
      await axios.put('/api/company/profile', this.profileForm)
      this.profileSuccess = 'Profile updated!'
      setTimeout(() => this.profileSuccess = '', 3000)
    },
  },
}
