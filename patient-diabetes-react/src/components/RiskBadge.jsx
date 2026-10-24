function RiskBadge({ level }) {
  return <span className={`badge badge-${level}`}>{level}</span>;
}

export default RiskBadge;
