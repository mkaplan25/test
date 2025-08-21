import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:syncfusion_flutter_charts/charts.dart';

class FazGrafikEkrani extends StatelessWidget {
  final Map<String, dynamic> calculationResult;
  final String inputSolute;
  final double inputTemp;
  final double inputWtX;
  final List<Map<String, dynamic>> phasePoints;
  final List<Map<String, dynamic>> phaseRegions;

  const FazGrafikEkrani({
    super.key,
    required this.calculationResult,
    required this.inputSolute,
    required this.inputTemp,
    required this.inputWtX,
    required this.phasePoints,
    required this.phaseRegions,
  });

  @override
  Widget build(BuildContext context) {
    print('🎯 FazGrafikEkrani - phasePoints geldi mi? ${phasePoints.length}');
    final String? summary = calculationResult['summary'];
    final String? imageBase64 = calculationResult['phase_diagram_image'];
    final List<dynamic> equilibriumData =
        calculationResult['equilibrium_data'] ?? [];

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("🔍 Girdi Özeti",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          SizedBox(height: 4),
          Text(
              "➕ Element: $inputSolute, Sıcaklık: ${inputTemp.toStringAsFixed(0)}°C, %${inputWtX.toStringAsFixed(2)}"),
          SizedBox(height: 16),
          if (summary != null)
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(summary, style: TextStyle(fontSize: 14)),
            ),
          SizedBox(height: 20),
          Text("📊 Denge Fazları",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          DataTable(
            columns: const [
              DataColumn(label: Text('Faz')),
              DataColumn(label: Text('Faz Oranı')),
              DataColumn(label: Text('Element (%)')),
            ],
            rows: equilibriumData.map((e) {
              return DataRow(cells: [
                DataCell(Text(e['Phase'] ?? "-")),
                DataCell(Text((e['PhaseFraction'] * 100).toStringAsFixed(2))),
                DataCell(Text((e['${inputSolute}AtPercentInPhase'] ?? 0.0)
                    .toStringAsFixed(2))),
              ]);
            }).toList(),
          ),
          SizedBox(height: 24),
          Text("🌡️ Faz Diyagramı",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          SizedBox(height: 8),
          if (phasePoints.isNotEmpty)
            SizedBox(
              height: 400,
              child: SfCartesianChart(
                title: ChartTitle(text: "Faz Diyagramı"),
                legend: const Legend(isVisible: true),
                tooltipBehavior: TooltipBehavior(enable: true),
                zoomPanBehavior: ZoomPanBehavior(
                  enablePanning: true, // 👆 parmakla kaydırma
                  enablePinching: true, // 🤏 iki parmakla yakınlaştır
                  enableDoubleTapZooming: true, // 🖱️ çift tıkla zoom
                  enableMouseWheelZooming: true, // 🖱️ tekerlek zoom (desktop)
                  zoomMode: ZoomMode.xy, // 📈 X ve Y eksenini birlikte zoom
                ),
                primaryXAxis: NumericAxis(
                  title: AxisTitle(text: "Ağırlıkça % $inputSolute"),
                  edgeLabelPlacement: EdgeLabelPlacement.shift,
                ),
                primaryYAxis: NumericAxis(
                  title: AxisTitle(text: "Sıcaklık (°C)"),
                ),
                series: [
                  // 🌈 1️⃣ Faz sınır çizgileri
                  ...phaseRegions.map((region) {
                    final label = region['label'];
                    final List<Map<String, dynamic>> points =
                        List<Map<String, dynamic>>.from(region['points']);

                    // X'e göre sırala
                    points.sort(
                        (a, b) => (a['x'] as num).compareTo(b['x'] as num));

                    return LineSeries<Map<String, dynamic>, double>(
                      dataSource: points,
                      xValueMapper: (point, _) =>
                          (point['x'] as num).toDouble(),
                      yValueMapper: (point, _) =>
                          (point['y'] as num).toDouble(),
                      name: label,
                      markerSettings: const MarkerSettings(
                          isVisible: false), // çizgisel gösterim
                      dataLabelSettings:
                          const DataLabelSettings(isVisible: false),
                    );
                  }),

                  // 🔴 2️⃣ Kullanıcının hesaplama yaptığı nokta (phasePoints)
                  ...phasePoints.map((point) {
                    return ScatterSeries<Map<String, dynamic>, double>(
                      dataSource: [point],
                      xValueMapper: (point, _) =>
                          (point['x'] as num).toDouble(),
                      yValueMapper: (point, _) =>
                          (point['y'] as num).toDouble(),
                      name: point['phase'],
                      markerSettings: const MarkerSettings(
                          height: 10, width: 10, shape: DataMarkerType.circle),
                      dataLabelMapper: (point, _) => point['phase'],
                      dataLabelSettings:
                          const DataLabelSettings(isVisible: true),
                    );
                  }),
                ],
              ),
            )
          else
            Text("Faz diyagramı verisi yok."),
        ],
      ),
    );
  }
}
