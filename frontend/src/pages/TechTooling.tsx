import { useQuery } from "@tanstack/react-query";

import { getOverview, getToolingConfig } from "../api/client";
import BarList from "../components/BarList";
import Donut from "../components/Donut";
import KpiCard from "../components/KpiCard";
import Panel from "../components/Panel";
import { SkeletonCards } from "../components/Skeleton";
import { formatCount, mapToBarItems } from "../lib/format";
import { theme } from "../theme";

export default function TechTooling() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["overview"],
    queryFn: getOverview,
  });
  const {
    data: toolingConfig,
    isLoading: toolingLoading,
    error: toolingError,
  } = useQuery({
    queryKey: ["tooling-config"],
    queryFn: getToolingConfig,
  });

  if (isLoading || toolingLoading) {
    return (
      <div>
        <h2 style={{ marginTop: "1.4rem" }}>Tech & Tooling</h2>
        <SkeletonCards count={3} />
      </div>
    );
  }
  if (error || !data || toolingError || !toolingConfig) {
    return <p>Erreur de chargement.</p>;
  }

  const languages = mapToBarItems(data.language_counts);
  const frameworks = mapToBarItems(data.framework_counts);
  const builtinTools = mapToBarItems(data.builtin_tool_counts);
  const userTools = mapToBarItems(data.user_tool_counts);
  const skills = mapToBarItems(data.skill_counts);
  const mcpServers = mapToBarItems(data.mcp_server_counts);
  const subagents = mapToBarItems(data.subagent_counts);
  const slashCommands = mapToBarItems(data.slash_command_counts);

  const langDonut = languages.map((it) => ({ name: it.label, value: it.value }));

  // `used: null` => usage not tracked by the backend (plugins/hooks have no
  // per-invocation counter), rendered as "—" rather than echoing `installed`.
  const installedVsUsed: { label: string; installed: number; used: number | null }[] = [
    {
      label: "Skills",
      installed: toolingConfig.skills.length,
      used: Object.keys(data.skill_counts).length,
    },
    {
      label: "Plugins activés",
      installed: toolingConfig.plugins_enabled.length,
      used: null,
    },
    {
      label: "Serveurs MCP",
      installed: toolingConfig.mcp_servers.length,
      used: Object.keys(data.mcp_server_counts).length,
    },
    {
      label: "Sous-agents",
      installed: toolingConfig.subagents.length,
      used: Object.keys(data.subagent_counts).length,
    },
    {
      label: "Hooks",
      installed: toolingConfig.hooks,
      used: null,
    },
  ];

  return (
    <div style={{ display: "grid", gap: 22 }}>
      <h2 style={{ marginTop: "1.4rem", marginBottom: 0 }}>Tech & Tooling</h2>

      {/* KPI row */}
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
        <KpiCard
          label="Langages"
          value={formatCount(Object.keys(data.language_counts).length)}
          sub="distincts"
          index={0}
        />
        <KpiCard
          label="Frameworks"
          value={formatCount(Object.keys(data.framework_counts).length)}
          sub="distincts"
          index={1}
        />
        <KpiCard
          label="Skills installés"
          value={formatCount(toolingConfig.skills.length)}
          index={2}
        />
        <KpiCard
          label="Serveurs MCP"
          value={formatCount(toolingConfig.mcp_servers.length)}
          sub="installés"
          index={3}
        />
        <KpiCard
          label="Plugins activés"
          value={formatCount(toolingConfig.plugins_enabled.length)}
          index={4}
        />
        <KpiCard
          label="Hooks"
          value={formatCount(toolingConfig.hooks)}
          index={5}
        />
      </div>

      {/* Language donut */}
      <Panel
        title="Mix des langages"
        right={`${Object.keys(data.language_counts).length} langages détectés`}
      >
        {langDonut.length > 0 ? (
          <Donut data={langDonut} height={220} formatValue={formatCount} />
        ) : (
          <p>Aucun langage détecté.</p>
        )}
      </Panel>

      {/* Frameworks bar list */}
      <Panel
        title="Frameworks"
        right="top 12 · toutes sessions"
      >
        {frameworks.length > 0 ? (
          <BarList
            items={frameworks}
            format={formatCount}
            color={theme.colors.amber}
          />
        ) : (
          <p>Aucun framework détecté.</p>
        )}
      </Panel>

      {/* Built-in vs user tools — two BarLists side by side */}
      <Panel title="Outils Claude Code">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 24,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: theme.colors.textMuted,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: 12,
              }}
            >
              Outils intégrés Claude Code
            </div>
            {builtinTools.length > 0 ? (
              <BarList
                items={builtinTools}
                format={formatCount}
                color={theme.colors.accent}
              />
            ) : (
              <p style={{ color: theme.colors.textMuted, fontSize: 13 }}>
                Aucun outil intégré enregistré.
              </p>
            )}
          </div>
          <div>
            <div
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: theme.colors.textMuted,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: 12,
              }}
            >
              Outils installés / créés par l'utilisateur
            </div>
            {userTools.length > 0 ? (
              <BarList
                items={userTools}
                format={formatCount}
                color={theme.colors.green}
              />
            ) : (
              <p style={{ color: theme.colors.textMuted, fontSize: 13 }}>
                Aucun outil utilisateur enregistré.
              </p>
            )}
          </div>
        </div>
      </Panel>

      {/* Skills */}
      <Panel title="Skills utilisés">
        {skills.length > 0 ? (
          <BarList items={skills} format={formatCount} color={theme.colors.accent} />
        ) : (
          <p>Aucun skill utilisé.</p>
        )}
      </Panel>

      {/* MCP servers */}
      <Panel title="Serveurs MCP utilisés">
        {mcpServers.length > 0 ? (
          <BarList items={mcpServers} format={formatCount} color={theme.chart[5]} />
        ) : (
          <p>Aucun serveur MCP utilisé.</p>
        )}
      </Panel>

      {/* Subagents */}
      <Panel title="Sous-agents">
        {subagents.length > 0 ? (
          <BarList items={subagents} format={formatCount} color={theme.chart[4]} />
        ) : (
          <p>Aucun sous-agent enregistré.</p>
        )}
      </Panel>

      {/* Slash commands */}
      <Panel title="Slash commands">
        {slashCommands.length > 0 ? (
          <BarList items={slashCommands} format={formatCount} color={theme.chart[3]} />
        ) : (
          <p>Aucune slash command enregistrée.</p>
        )}
      </Panel>

      {/* Installed vs Used comparison */}
      <Panel title="Installé vs Utilisé" right="comparaison config ↔ activité">
        <table className="data-table">
          <thead>
            <tr>
              <th align="left">Catégorie</th>
              <th>Installés / configurés</th>
              <th>Distincts utilisés</th>
            </tr>
          </thead>
          <tbody>
            {installedVsUsed.map((row) => (
              <tr key={row.label}>
                <td style={{ textAlign: "left", fontFamily: theme.font.mono, fontSize: 13 }}>
                  {row.label}
                </td>
                <td style={{ fontFamily: theme.font.mono, fontSize: 13 }}>
                  {formatCount(row.installed)}
                </td>
                <td
                  style={{
                    fontFamily: theme.font.mono,
                    fontSize: 13,
                    color:
                      row.used == null
                        ? theme.colors.textFaint
                        : row.used > row.installed
                          ? theme.colors.amber
                          : theme.colors.text,
                  }}
                  title={row.used == null ? "non suivi" : undefined}
                >
                  {row.used == null ? "—" : formatCount(row.used)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ marginTop: 12, marginBottom: 0, fontSize: 12, color: theme.colors.textMuted }}>
          L'utilisation des plugins et hooks n'est pas suivie (pas de compteur par invocation côté backend).
        </p>
      </Panel>
    </div>
  );
}
