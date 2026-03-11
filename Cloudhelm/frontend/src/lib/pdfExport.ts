import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { ReliabilityMetrics } from '../types/overview';
import type { ServiceHealth } from '../types/health';

export function generateSLAPDF(
  reliability: ReliabilityMetrics | null,
  healthSummary: ServiceHealth[],
  systemStatus: string
) {
  const doc = new jsPDF();
  const timestamp = new Date().toLocaleString();

  // Header
  doc.setFontSize(20);
  doc.setTextColor(34, 211, 238); // Cyan
  doc.text('SLA Status Report', 14, 22);
  
  doc.setFontSize(10);
  doc.setTextColor(100, 116, 139); // Muted
  doc.text(`Generated on: ${timestamp}`, 14, 30);
  doc.text(`System Status: ${systemStatus}`, 14, 35);

  // 1. Executive Summary Table
  doc.setFontSize(14);
  doc.setTextColor(0, 0, 0);
  doc.text('1. Executive Summary', 14, 48);

  const executiveData = [
    ['Global Availability', reliability ? `${reliability.availability.percentage}%` : 'N/A'],
    ['MTTR (Average)', reliability ? reliability.mttr.average : 'N/A'],
    ['Active Incidents', reliability ? reliability.open_incidents.length.toString() : '0'],
    ['Overall Status', systemStatus]
  ];

  autoTable(doc, {
    startY: 52,
    head: [['Metric', 'Value']],
    body: executiveData,
    theme: 'striped',
    headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0], fontStyle: 'bold' },
    styles: { fontSize: 10, cellPadding: 5 }
  });

  // 2. Service Health Table
  let finalY = (doc as any).lastAutoTable.finalY || 52;
  doc.setFontSize(14);
  doc.text('2. Service Health Summary', 14, finalY + 15);

  const serviceData = healthSummary.map(s => [
    s.service_name,
    s.status.toUpperCase(),
    `${(s.health_score * 100).toFixed(2)}%`,
    `${(s.error_rate * 100).toFixed(2)}%`
  ]);

  autoTable(doc, {
    startY: finalY + 20,
    head: [['Service Name', 'Status', 'Health Score', 'Error Rate']],
    body: serviceData,
    theme: 'grid',
    headStyles: { fillColor: [34, 211, 238], textColor: [255, 255, 255] },
    styles: { fontSize: 9 }
  });

  // 3. Critical Incidents Table
  if (reliability?.open_incidents && reliability.open_incidents.length > 0) {
    finalY = (doc as any).lastAutoTable.finalY;
    doc.setFontSize(14);
    doc.text('3. Active Critical Incidents', 14, finalY + 15);

    const incidentData = reliability.open_incidents.map(i => [
      i.severity.toUpperCase(),
      i.title,
      i.service,
      i.duration
    ]);

    autoTable(doc, {
      startY: finalY + 20,
      head: [['Severity', 'Incident Title', 'Affected Service', 'Duration']],
      body: incidentData,
      theme: 'grid',
      headStyles: { fillColor: [248, 113, 113], textColor: [255, 255, 255] }, // Red for incidents
      styles: { fontSize: 9 }
    });
  }

  // Footer
  const pageCount = (doc as any).internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(150);
    doc.text(
      `Confidential - CloudHelm SLA Report - Page ${i} of ${pageCount}`,
      doc.internal.pageSize.getWidth() / 2,
      doc.internal.pageSize.getHeight() - 10,
      { align: 'center' }
    );
  }

  doc.save(`SLA_Report_${new Date().toISOString().split('T')[0]}.pdf`);
}
