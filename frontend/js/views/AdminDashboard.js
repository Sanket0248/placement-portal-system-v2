/**
 * AdminDashboard.js — Admin dashboard (6 tabs inside AppShell).
 *
 * Tabs: Overview (stats + pending approvals + monthly report + charts),
 *       Students, Companies, Drives, Applications, Search.
 * Includes 4 detail modals and 2 Chart.js charts (doughnut + bar).
 * Charts are destroyed and re-created when switching back to Overview tab.
 * Role accent color: cobalt (set via data-role="admin" in AppShell).
 */
const AdminDashboardView = {
  template: `
  <app-shell role="admin" title="Admin" :nav-items="tabs" v-model="activeTab">

    <!-- ===== OVERVIEW ===== -->
    <template v-if="activeTab === 'overview'">
      <div class="row g-3 mb-4">
        <div class="col-sm-6 col-lg-3" v-for="s in stats" :key="s.label">
          <div class="stat-card">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <div class="stat-label">{{ s.label }}</div>
                <div class="stat-value">{{ s.value }}</div>
              </div>
              <i :class="s.icon + ' stat-icon'"></i>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <!-- Pending approvals -->
        <div class="col-md-6">
          <div class="pp-card">
            <div class="pp-card-head"><h6><i class="bi bi-clock-history me-2"></i>Pending Approvals</h6></div>
            <div v-if="pendingCompanies.length === 0 && pendingDrives.length === 0" class="empty-state py-3">
              <i class="bi bi-check-circle"></i>All caught up.
            </div>
            <div v-for="c in pendingCompanies" :key="'c'+c.id"
              class="d-flex justify-content-between align-items-center py-2" style="border-bottom:1px solid var(--line);">
              <span><i class="bi bi-building me-2" style="color:var(--warn)"></i>{{ c.company_name }}</span>
              <div class="d-flex gap-1">
                <button class="btn btn-sm" style="background:var(--ok);color:#fff;" @click="approveCompany(c.id)">Approve</button>
                <button class="btn btn-sm" style="background:var(--danger);color:#fff;" @click="rejectCompany(c.id)">Reject</button>
              </div>
            </div>
            <div v-for="d in pendingDrives" :key="'d'+d.id"
              class="d-flex justify-content-between align-items-center py-2" style="border-bottom:1px solid var(--line);">
              <span><i class="bi bi-briefcase me-2" style="color:var(--info)"></i>{{ d.job_title }}</span>
              <div class="d-flex gap-1">
                <button class="btn btn-sm" style="background:var(--ok);color:#fff;" @click="approveDrive(d.id)">Approve</button>
                <button class="btn btn-sm" style="background:var(--danger);color:#fff;" @click="rejectDrive(d.id)">Reject</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Monthly stats -->
        <div class="col-md-6">
          <div class="pp-card">
            <div class="pp-card-head"><h6><i class="bi bi-bar-chart me-2"></i>Monthly Stats</h6></div>
            <div v-if="monthly">
              <div class="d-flex justify-content-between py-2" style="border-bottom:1px solid var(--line);">
                <span class="text-muted">Month</span><strong>{{ monthly.month }}</strong>
              </div>
              <div class="d-flex justify-content-between py-2" style="border-bottom:1px solid var(--line);">
                <span class="text-muted">Drives conducted</span><strong>{{ monthly.drives_conducted }}</strong>
              </div>
              <div class="d-flex justify-content-between py-2" style="border-bottom:1px solid var(--line);">
                <span class="text-muted">Total applications</span><strong>{{ monthly.total_applications }}</strong>
              </div>
              <div class="d-flex justify-content-between py-2">
                <span class="text-muted">Students selected</span><strong style="color:var(--ok)">{{ monthly.students_selected }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="row g-3">
        <div class="col-md-6">
          <div class="pp-card" style="padding:1.25rem;">
            <div class="pp-card-head"><h6><i class="bi bi-pie-chart me-2"></i>Application Status</h6></div>
            <div style="max-width:280px;margin:0 auto;"><canvas id="appStatusChart"></canvas></div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="pp-card" style="padding:1.25rem;">
            <div class="pp-card-head"><h6><i class="bi bi-bar-chart me-2"></i>Students by Branch</h6></div>
            <div style="max-width:380px;margin:0 auto;"><canvas id="branchChart"></canvas></div>
          </div>
        </div>
      </div>
    </template>

    <!-- ===== STUDENTS ===== -->
    <template v-if="activeTab === 'students'">
      <div class="section-head">
        <h5>All Students</h5>
        <input v-model="studentSearch" type="text" class="form-control form-control-sm" style="max-width:220px;"
          placeholder="Search students…" />
      </div>
      <div class="pp-card" style="overflow-x:auto">
        <table class="pp-table">
          <thead><tr><th>Name</th><th>Roll No</th><th>Branch</th><th>CGPA</th><th>Year</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="s in filteredStudents" :key="s.id">
              <td class="fw-semibold">{{ s.full_name }}</td>
              <td>{{ s.roll_number }}</td><td>{{ s.branch }}</td>
              <td class="tnum">{{ s.cgpa }}</td><td>{{ s.year_of_study }}</td>
              <td><span class="pill" :class="s.is_blacklisted ? 'pill-danger' : 'pill-ok'">{{ s.is_blacklisted ? 'Blacklisted' : 'Active' }}</span></td>
              <td>
                <div class="d-flex gap-1">
                  <button class="btn btn-outline-primary btn-sm" @click="viewStudentDetail(s)"><i class="bi bi-eye me-1"></i>Details</button>
                  <button class="btn btn-sm" :class="s.is_blacklisted ? 'btn-outline-success' : 'btn-outline-danger'" @click="toggleStudentBlacklist(s)">
                    {{ s.is_blacklisted ? 'Reactivate' : 'Blacklist' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ===== COMPANIES ===== -->
    <template v-if="activeTab === 'companies'">
      <div class="section-head">
        <h5>All Companies</h5>
        <input v-model="companySearch" type="text" class="form-control form-control-sm" style="max-width:220px;"
          placeholder="Search companies…" />
      </div>
      <div class="pp-card" style="overflow-x:auto">
        <table class="pp-table">
          <thead><tr><th>Company</th><th>HR Name</th><th>Industry</th><th>Approval</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="c in filteredCompanies" :key="c.id">
              <td class="fw-semibold">{{ c.company_name }}</td>
              <td>{{ c.hr_name }}</td><td>{{ c.industry }}</td>
              <td><span class="pill" :class="'pill-'+c.approval_status">{{ c.approval_status }}</span></td>
              <td><span class="pill" :class="c.is_blacklisted ? 'pill-danger' : 'pill-ok'">{{ c.is_blacklisted ? 'Blacklisted' : 'Active' }}</span></td>
              <td>
                <div class="d-flex gap-1 flex-wrap">
                  <button class="btn btn-outline-primary btn-sm" @click="viewCompanyDetail(c)"><i class="bi bi-eye me-1"></i>Details</button>
                  <button v-if="c.approval_status==='pending'" class="btn btn-sm" style="background:var(--ok);color:#fff" @click="approveCompany(c.id)">Approve</button>
                  <button v-if="c.approval_status==='pending'" class="btn btn-sm" style="background:var(--danger);color:#fff" @click="rejectCompany(c.id)">Reject</button>
                  <button class="btn btn-sm" :class="c.is_blacklisted ? 'btn-outline-success' : 'btn-outline-danger'" @click="toggleCompanyBlacklist(c)">
                    {{ c.is_blacklisted ? 'Reactivate' : 'Blacklist' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ===== DRIVES ===== -->
    <template v-if="activeTab === 'drives'">
      <div class="section-head"><h5>All Placement Drives</h5></div>
      <div class="pp-card" style="overflow-x:auto">
        <table class="pp-table">
          <thead><tr><th>Job Title</th><th>Company</th><th>Deadline</th><th>Package</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="d in drives" :key="d.id">
              <td class="fw-semibold">{{ d.job_title }}</td>
              <td>{{ d.company_name }}</td>
              <td>{{ d.application_deadline }}</td>
              <td class="tnum">{{ d.package_lpa }} LPA</td>
              <td><span class="pill" :class="'pill-'+d.status">{{ d.status }}</span></td>
              <td>
                <div class="d-flex gap-1 flex-wrap">
                  <button class="btn btn-outline-primary btn-sm" @click="viewDriveDetail(d)"><i class="bi bi-eye me-1"></i>Details</button>
                  <button v-if="d.status==='pending'" class="btn btn-sm" style="background:var(--ok);color:#fff" @click="approveDrive(d.id)">Approve</button>
                  <button v-if="d.status==='pending'" class="btn btn-sm" style="background:var(--danger);color:#fff" @click="rejectDrive(d.id)">Reject</button>
                  <button v-if="d.status==='approved'" class="btn btn-outline-secondary btn-sm" @click="closeDrive(d.id)">
                    <i class="bi bi-check-circle me-1"></i>Complete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ===== APPLICATIONS ===== -->
    <template v-if="activeTab === 'applications'">
      <div class="section-head"><h5>All Applications</h5></div>
      <div class="pp-card" style="overflow-x:auto">
        <table class="pp-table">
          <thead><tr><th>Student</th><th>Company</th><th>Drive</th><th>Date</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
            <tr v-for="a in applications" :key="a.id">
              <td class="fw-semibold">{{ a.student_name }}</td>
              <td>{{ a.company_name }}</td><td>{{ a.drive_title }}</td>
              <td>{{ a.application_date }}</td>
              <td><span class="pill" :class="'pill-'+a.status">{{ a.status }}</span></td>
              <td><button class="btn btn-outline-primary btn-sm" @click="viewApplicationDetail(a)"><i class="bi bi-eye me-1"></i>Details</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ===== SEARCH ===== -->
    <template v-if="activeTab === 'search'">
      <div class="pp-card mb-4">
        <div class="pp-card-head"><h6><i class="bi bi-search me-2"></i>Search Students &amp; Companies</h6></div>
        <div class="row g-2">
          <div class="col-md-6"><input v-model="searchQuery" type="text" class="form-control"
            placeholder="Name, roll number, branch, industry…" @keyup.enter="doSearch" /></div>
          <div class="col-md-3">
            <select v-model="searchType" class="form-select">
              <option value="all">All</option><option value="students">Students only</option><option value="companies">Companies only</option>
            </select>
          </div>
          <div class="col-md-3"><button class="btn btn-accent w-100" @click="doSearch"><i class="bi bi-search me-1"></i>Search</button></div>
        </div>
      </div>

      <template v-if="searchDone">
        <div v-if="searchResults.students && searchResults.students.length > 0" class="mb-4">
          <div class="section-head"><h5><i class="bi bi-people me-2"></i>Students <span class="pill pill-applied ms-1">{{ searchResults.students.length }}</span></h5></div>
          <div class="pp-card" style="overflow-x:auto">
            <table class="pp-table">
              <thead><tr><th>Name</th><th>Roll No</th><th>Branch</th><th>CGPA</th><th>Year</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="s in searchResults.students" :key="s.id">
                  <td>{{ s.full_name }}</td><td>{{ s.roll_number }}</td><td>{{ s.branch }}</td>
                  <td class="tnum">{{ s.cgpa }}</td><td>{{ s.year_of_study }}</td>
                  <td><span class="pill" :class="s.is_blacklisted ? 'pill-danger' : 'pill-ok'">{{ s.is_blacklisted ? 'Blacklisted' : 'Active' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="searchResults.companies && searchResults.companies.length > 0">
          <div class="section-head"><h5><i class="bi bi-building me-2"></i>Companies <span class="pill pill-applied ms-1">{{ searchResults.companies.length }}</span></h5></div>
          <div class="pp-card" style="overflow-x:auto">
            <table class="pp-table">
              <thead><tr><th>Company</th><th>HR Name</th><th>Industry</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="c in searchResults.companies" :key="c.id">
                  <td>{{ c.company_name }}</td><td>{{ c.hr_name }}</td><td>{{ c.industry }}</td>
                  <td><span class="pill" :class="'pill-'+c.approval_status">{{ c.approval_status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="searchResults.students?.length === 0 && searchResults.companies?.length === 0" class="empty-state">
          <i class="bi bi-search"></i>No results for "{{ searchQuery }}"
        </div>
      </template>
    </template>

    <!-- ===== MODALS ===== -->

    <!-- Student detail modal -->
    <div v-if="selectedStudent" class="pp-modal-back" @click.self="selectedStudent = null">
      <div class="pp-modal">
        <div class="pp-modal-head">
          <h5><i class="bi bi-person-circle me-2"></i>Student Details</h5>
          <button class="btn-close btn-close-white" @click="selectedStudent = null"></button>
        </div>
        <div class="pp-modal-body">
          <div class="text-center mb-3">
            <i class="bi bi-person-circle" style="font-size:3.5rem;color:var(--accent);"></i>
            <h5 class="mt-2 fw-bold font-display">{{ selectedStudent.full_name }}</h5>
            <span class="pill" :class="selectedStudent.is_blacklisted ? 'pill-danger' : 'pill-ok'">
              {{ selectedStudent.is_blacklisted ? 'Blacklisted' : 'Active' }}
            </span>
          </div>
          <table class="pp-table">
            <tbody>
              <tr><td class="fw-semibold" style="width:40%">Email</td><td>{{ selectedStudent.email }}</td></tr>
              <tr><td class="fw-semibold">Roll Number</td><td>{{ selectedStudent.roll_number }}</td></tr>
              <tr><td class="fw-semibold">Branch</td><td>{{ selectedStudent.branch }}</td></tr>
              <tr><td class="fw-semibold">CGPA</td><td>{{ selectedStudent.cgpa }}</td></tr>
              <tr><td class="fw-semibold">Year</td><td>{{ selectedStudent.year_of_study }}</td></tr>
              <tr><td class="fw-semibold">Phone</td><td>{{ selectedStudent.phone || 'N/A' }}</td></tr>
              <tr><td class="fw-semibold">Resume</td>
                <td>
                  <a v-if="selectedStudent.resume_path" :href="'/api/student/resume/'+selectedStudent.resume_path"
                    target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-file-earmark-pdf me-1"></i>View</a>
                  <span v-else class="pill pill-warn">Not uploaded</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pp-modal-foot">
          <button class="btn btn-sm" :class="selectedStudent.is_blacklisted ? 'btn-outline-success' : 'btn-outline-danger'"
            @click="toggleStudentBlacklist(selectedStudent); selectedStudent = null">
            {{ selectedStudent.is_blacklisted ? 'Reactivate' : 'Blacklist' }}
          </button>
          <button class="btn btn-outline-secondary btn-sm" @click="selectedStudent = null">Close</button>
        </div>
      </div>
    </div>

    <!-- Company detail modal -->
    <div v-if="selectedCompany" class="pp-modal-back" @click.self="selectedCompany = null">
      <div class="pp-modal">
        <div class="pp-modal-head">
          <h5><i class="bi bi-building me-2"></i>Company Details</h5>
          <button class="btn-close btn-close-white" @click="selectedCompany = null"></button>
        </div>
        <div class="pp-modal-body">
          <div class="text-center mb-3">
            <i class="bi bi-building" style="font-size:3.5rem;color:var(--accent);"></i>
            <h5 class="mt-2 fw-bold font-display">{{ selectedCompany.company_name }}</h5>
            <span class="pill" :class="'pill-'+selectedCompany.approval_status">{{ selectedCompany.approval_status }}</span>
          </div>
          <table class="pp-table">
            <tbody>
              <tr><td class="fw-semibold" style="width:40%">HR Name</td><td>{{ selectedCompany.hr_name }}</td></tr>
              <tr><td class="fw-semibold">HR Email</td><td>{{ selectedCompany.hr_email }}</td></tr>
              <tr><td class="fw-semibold">Website</td><td>{{ selectedCompany.website || 'N/A' }}</td></tr>
              <tr><td class="fw-semibold">Industry</td><td>{{ selectedCompany.industry || 'N/A' }}</td></tr>
              <tr><td class="fw-semibold">Description</td><td>{{ selectedCompany.description || 'N/A' }}</td></tr>
              <tr><td class="fw-semibold">Registered</td><td>{{ selectedCompany.registered_at?.split('T')[0] }}</td></tr>
            </tbody>
          </table>
        </div>
        <div class="pp-modal-foot">
          <button v-if="selectedCompany.approval_status==='pending'" class="btn btn-sm" style="background:var(--ok);color:#fff"
            @click="approveCompany(selectedCompany.id); selectedCompany = null">Approve</button>
          <button v-if="selectedCompany.approval_status==='pending'" class="btn btn-sm" style="background:var(--danger);color:#fff"
            @click="rejectCompany(selectedCompany.id); selectedCompany = null">Reject</button>
          <button class="btn btn-sm" :class="selectedCompany.is_blacklisted ? 'btn-outline-success' : 'btn-outline-danger'"
            @click="toggleCompanyBlacklist(selectedCompany); selectedCompany = null">
            {{ selectedCompany.is_blacklisted ? 'Reactivate' : 'Blacklist' }}
          </button>
          <button class="btn btn-outline-secondary btn-sm" @click="selectedCompany = null">Close</button>
        </div>
      </div>
    </div>

    <!-- Drive detail modal -->
    <div v-if="selectedDrive" class="pp-modal-back" @click.self="selectedDrive = null">
      <div class="pp-modal">
        <div class="pp-modal-head">
          <h5><i class="bi bi-briefcase me-2"></i>Drive Details</h5>
          <button class="btn-close btn-close-white" @click="selectedDrive = null"></button>
        </div>
        <div class="pp-modal-body">
          <div class="text-center mb-3">
            <i class="bi bi-briefcase" style="font-size:3.5rem;color:var(--accent);"></i>
            <h5 class="mt-2 fw-bold font-display">{{ selectedDrive.job_title }}</h5>
            <span class="pill" :class="'pill-'+selectedDrive.status">{{ selectedDrive.status }}</span>
          </div>
          <table class="pp-table">
            <tbody>
              <tr><td class="fw-semibold" style="width:40%">Company</td><td>{{ selectedDrive.company_name }}</td></tr>
              <tr><td class="fw-semibold">Job Type</td><td>{{ selectedDrive.job_type }}</td></tr>
              <tr><td class="fw-semibold">Package</td><td>{{ selectedDrive.package_lpa }} LPA</td></tr>
              <tr><td class="fw-semibold">Min CGPA</td><td>{{ selectedDrive.min_cgpa }}</td></tr>
              <tr><td class="fw-semibold">Branches</td>
                <td><span v-for="b in selectedDrive.eligible_branches" :key="b" class="pill pill-neutral me-1">{{ b }}</span></td>
              </tr>
              <tr><td class="fw-semibold">Year</td><td>Year {{ selectedDrive.eligible_year }}</td></tr>
              <tr><td class="fw-semibold">Deadline</td><td>{{ selectedDrive.application_deadline }}</td></tr>
              <tr><td class="fw-semibold">Description</td><td>{{ selectedDrive.job_description }}</td></tr>
            </tbody>
          </table>
        </div>
        <div class="pp-modal-foot">
          <button v-if="selectedDrive.status==='pending'" class="btn btn-sm" style="background:var(--ok);color:#fff"
            @click="approveDrive(selectedDrive.id); selectedDrive = null">Approve</button>
          <button v-if="selectedDrive.status==='pending'" class="btn btn-sm" style="background:var(--danger);color:#fff"
            @click="rejectDrive(selectedDrive.id); selectedDrive = null">Reject</button>
          <button v-if="selectedDrive.status==='approved'" class="btn btn-outline-secondary btn-sm"
            @click="closeDrive(selectedDrive.id); selectedDrive = null"><i class="bi bi-check-circle me-1"></i>Complete</button>
          <button class="btn btn-outline-secondary btn-sm" @click="selectedDrive = null">Close</button>
        </div>
      </div>
    </div>

    <!-- Application detail modal -->
    <div v-if="selectedApplication" class="pp-modal-back" @click.self="selectedApplication = null">
      <div class="pp-modal">
        <div class="pp-modal-head">
          <h5><i class="bi bi-file-earmark-person me-2"></i>Application Details</h5>
          <button class="btn-close btn-close-white" @click="selectedApplication = null"></button>
        </div>
        <div class="pp-modal-body">
          <div class="text-center mb-3">
            <i class="bi bi-person-circle" style="font-size:3.5rem;color:var(--accent);"></i>
            <h5 class="mt-2 fw-bold font-display">{{ selectedApplication.student_name }}</h5>
            <span class="pill" :class="'pill-'+selectedApplication.status">{{ selectedApplication.status }}</span>
          </div>
          <table class="pp-table">
            <tbody>
              <tr><td class="fw-semibold" style="width:40%">Student</td><td>{{ selectedApplication.student_name }}</td></tr>
              <tr><td class="fw-semibold">Resume</td>
                <td>
                  <a v-if="selectedApplication.resume_snapshot" :href="'/api/student/resume/'+selectedApplication.resume_snapshot"
                    target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-file-earmark-pdf me-1"></i>View</a>
                  <span v-else class="text-muted">None</span>
                </td>
              </tr>
              <tr><td class="fw-semibold">Company</td><td>{{ selectedApplication.company_name }}</td></tr>
              <tr><td class="fw-semibold">Drive</td><td>{{ selectedApplication.drive_title }}</td></tr>
              <tr><td class="fw-semibold">Applied on</td><td>{{ selectedApplication.application_date }}</td></tr>
              <tr><td class="fw-semibold">Status</td><td><span class="pill" :class="'pill-'+selectedApplication.status">{{ selectedApplication.status }}</span></td></tr>
            </tbody>
          </table>
        </div>
        <div class="pp-modal-foot">
          <button class="btn btn-outline-secondary btn-sm" @click="selectedApplication = null">Close</button>
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
        { key: 'students', label: 'Students', icon: 'bi bi-people' },
        { key: 'companies', label: 'Companies', icon: 'bi bi-building' },
        { key: 'drives', label: 'Drives', icon: 'bi bi-briefcase' },
        { key: 'applications', label: 'Applications', icon: 'bi bi-file-earmark-text' },
        { key: 'search', label: 'Search', icon: 'bi bi-search' },
      ],
      dashboardData: {},
      students: [],
      companies: [],
      drives: [],
      applications: [],
      monthly: null,
      studentSearch: '',
      companySearch: '',
      selectedStudent: null,
      selectedCompany: null,
      selectedDrive: null,
      selectedApplication: null,
      searchQuery: '',
      searchType: 'all',
      searchResults: { students: [], companies: [] },
      searchDone: false,
      chartInstances: {},
    }
  },
  computed: {
    stats() {
      return [
        { label: 'Total Students', value: this.dashboardData.total_students || 0, icon: 'bi bi-people-fill' },
        { label: 'Total Companies', value: this.dashboardData.total_companies || 0, icon: 'bi bi-building' },
        { label: 'Total Drives', value: this.dashboardData.total_drives || 0, icon: 'bi bi-briefcase-fill' },
        { label: 'Students Selected', value: this.dashboardData.selected_students || 0, icon: 'bi bi-trophy-fill' },
      ]
    },
    pendingCompanies() { return this.companies.filter(c => c.approval_status === 'pending') },
    pendingDrives() { return this.drives.filter(d => d.status === 'pending') },
    filteredStudents() {
      const q = this.studentSearch.toLowerCase()
      if (!q) return this.students
      return this.students.filter(s =>
        s.full_name.toLowerCase().includes(q) || s.roll_number.toLowerCase().includes(q) || s.branch.toLowerCase().includes(q)
      )
    },
    filteredCompanies() {
      const q = this.companySearch.toLowerCase()
      if (!q) return this.companies
      return this.companies.filter(c =>
        c.company_name.toLowerCase().includes(q) || (c.industry || '').toLowerCase().includes(q)
      )
    },
  },
  async mounted() {
    await this.loadAll()
    this.$nextTick(() => this.renderCharts())
  },
  watch: {
    activeTab(v) {
      if (v === 'overview') this.$nextTick(() => this.renderCharts())
    },
  },
  methods: {
    renderCharts() {
      if (this.chartInstances.appStatus) { this.chartInstances.appStatus.destroy(); this.chartInstances.appStatus = null }
      if (this.chartInstances.branch) { this.chartInstances.branch.destroy(); this.chartInstances.branch = null }

      const appCtx = document.getElementById('appStatusChart')
      if (appCtx) {
        const counts = { applied: 0, shortlisted: 0, selected: 0, rejected: 0 }
        this.applications.forEach(a => { if (counts[a.status] !== undefined) counts[a.status]++ })
        this.chartInstances.appStatus = new Chart(appCtx, {
          type: 'doughnut',
          data: {
            labels: ['Applied', 'Shortlisted', 'Selected', 'Rejected'],
            datasets: [{ data: [counts.applied, counts.shortlisted, counts.selected, counts.rejected],
              backgroundColor: ['#2e56d6', '#b07515', '#12855f', '#d0424a'] }],
          },
          options: { responsive: true, plugins: { legend: { position: 'bottom' } } },
        })
      }

      const branchCtx = document.getElementById('branchChart')
      if (branchCtx) {
        const bc = {}
        this.students.forEach(s => { bc[s.branch] = (bc[s.branch] || 0) + 1 })
        this.chartInstances.branch = new Chart(branchCtx, {
          type: 'bar',
          data: {
            labels: Object.keys(bc),
            datasets: [{ label: 'Students', data: Object.values(bc), backgroundColor: '#2e56d6' }],
          },
          options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
        })
      }
    },
    async loadAll() {
      const [dash, students, companies, drives, apps, monthly] = await Promise.all([
        axios.get('/api/admin/dashboard'),
        axios.get('/api/admin/students'),
        axios.get('/api/admin/companies'),
        axios.get('/api/admin/drives'),
        axios.get('/api/admin/applications'),
        axios.get('/api/admin/reports/monthly'),
      ])
      this.dashboardData = dash.data
      this.students = students.data
      this.companies = companies.data
      this.drives = drives.data
      this.applications = apps.data
      this.monthly = monthly.data
    },
    viewStudentDetail(s) { this.selectedStudent = s },
    viewCompanyDetail(c) { this.selectedCompany = c },
    viewDriveDetail(d) { this.selectedDrive = d },
    viewApplicationDetail(a) { this.selectedApplication = a },
    async approveCompany(id) { await axios.patch('/api/admin/companies/'+id+'/approve'); await this.loadAll() },
    async rejectCompany(id) { await axios.patch('/api/admin/companies/'+id+'/reject'); await this.loadAll() },
    async approveDrive(id) { await axios.patch('/api/admin/drives/'+id+'/approve'); await this.loadAll() },
    async rejectDrive(id) { await axios.patch('/api/admin/drives/'+id+'/reject'); await this.loadAll() },
    async closeDrive(id) { await axios.patch('/api/admin/drives/'+id+'/close'); await this.loadAll() },
    async toggleStudentBlacklist(s) {
      await axios.patch('/api/admin/students/'+s.id+'/blacklist', { is_blacklisted: !s.is_blacklisted })
      await this.loadAll()
    },
    async toggleCompanyBlacklist(c) {
      await axios.patch('/api/admin/companies/'+c.id+'/blacklist', { is_blacklisted: !c.is_blacklisted })
      await this.loadAll()
    },
    async doSearch() {
      if (!this.searchQuery.trim()) return
      const res = await axios.get('/api/admin/search', { params: { q: this.searchQuery, type: this.searchType } })
      this.searchResults = res.data
      this.searchDone = true
    },
  },
}
