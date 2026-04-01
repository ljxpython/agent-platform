import { WorkspaceShellV2 } from "@/components/platform/workspace-shell-v2";

export default function HomePage() {
  return (
    <WorkspaceShellV2>
      <section className="landing">
        <div className="landing__header">
          <div>
            <div className="landing__eyebrow">Home</div>
            <h1>Overview</h1>
            <p>统一承载项目、用户、助手和治理数据的企业工作台入口，当前用于校准 v2 的页面壳子、主题系统和视觉基线。</p>
          </div>

          <div className="landing__header-actions">
            <button className="landing__button landing__button--ghost" type="button">
              See all
            </button>
            <button className="landing__button landing__button--primary" type="button">
              New request
            </button>
          </div>
        </div>

        <section className="landing__stats-grid">
          <article className="landing__stat-card">
            <div className="landing__stat-label">Active Projects</div>
            <div className="landing__stat-value">12</div>
            <div className="landing__stat-meta landing__stat-meta--positive">3 newly created this week</div>
          </article>
          <article className="landing__stat-card">
            <div className="landing__stat-label">Assistants</div>
            <div className="landing__stat-value">37</div>
            <div className="landing__stat-meta">5 pending synchronization</div>
          </article>
          <article className="landing__stat-card">
            <div className="landing__stat-label">Runtime Threads</div>
            <div className="landing__stat-value">128</div>
            <div className="landing__stat-meta">stable throughput</div>
          </article>
          <article className="landing__stat-card">
            <div className="landing__stat-label">Awaiting Review</div>
            <div className="landing__stat-value">3</div>
            <div className="landing__stat-meta landing__stat-meta--danger">requires manual action</div>
          </article>
        </section>

        <section className="landing__main-grid">
          <article className="landing__panel landing__panel--wide">
            <div className="landing__panel-header">
              <div>
                <h2>Projects</h2>
                <p>展示 v2 后续会承接的标准企业后台节奏：搜索、筛选、表格和行操作。</p>
              </div>

              <div className="landing__toolbar">
                <input
                  className="landing__input"
                  type="text"
                  placeholder="Search projects, users or descriptions"
                />
                <button className="landing__button landing__button--ghost" type="button">
                  Filter
                </button>
                <button className="landing__button landing__button--ghost" type="button">
                  Refresh
                </button>
              </div>
            </div>

            <div className="landing__table-wrapper">
              <table className="landing__table">
                <thead>
                  <tr>
                    <th>Project</th>
                    <th>Owner</th>
                    <th>Status</th>
                    <th>Updated</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>智能测试平台</td>
                    <td>张三</td>
                    <td>
                      <span className="landing__status landing__status--success">active</span>
                    </td>
                    <td>今天 14:22</td>
                    <td>
                      <div className="landing__table-actions">
                        <button className="landing__text-button" type="button">
                          View
                        </button>
                        <button className="landing__text-button" type="button">
                          Manage
                        </button>
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td>用例生成平台</td>
                    <td>李四</td>
                    <td>
                      <span className="landing__status landing__status--warning">review</span>
                    </td>
                    <td>今天 10:18</td>
                    <td>
                      <div className="landing__table-actions">
                        <button className="landing__text-button" type="button">
                          View
                        </button>
                        <button className="landing__text-button" type="button">
                          Manage
                        </button>
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td>SQL Agent 工作台</td>
                    <td>王五</td>
                    <td>
                      <span className="landing__status landing__status--neutral">idle</span>
                    </td>
                    <td>昨天 21:40</td>
                    <td>
                      <div className="landing__table-actions">
                        <button className="landing__text-button" type="button">
                          View
                        </button>
                        <button className="landing__text-button" type="button">
                          Manage
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>

          <article className="landing__panel">
            <div className="landing__panel-header landing__panel-header--compact">
              <div>
                <h2>Awaiting Requests</h2>
                <p>适合承载待审批、审计、同步异常等侧边信息列表。</p>
              </div>
            </div>

            <ul className="landing__activity-list">
              <li>
                <span className="landing__activity-tag">Sync</span>
                <div>
                  <strong>assistant/test_case_agent</strong>
                  <p>配置变更后待同步到 runtime catalog</p>
                </div>
              </li>
              <li>
                <span className="landing__activity-tag landing__activity-tag--warning">Audit</span>
                <div>
                  <strong>权限提升申请</strong>
                  <p>项目「智能测试平台」存在角色调整请求</p>
                </div>
              </li>
              <li>
                <span className="landing__activity-tag landing__activity-tag--danger">Alert</span>
                <div>
                  <strong>线程失败重试</strong>
                  <p>过去 1 小时内出现 3 次超时</p>
                </div>
              </li>
            </ul>
          </article>
        </section>
      </section>
    </WorkspaceShellV2>
  );
}
