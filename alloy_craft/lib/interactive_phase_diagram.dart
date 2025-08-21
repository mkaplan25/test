import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:syncfusion_flutter_charts/charts.dart';

class InteraktifFazGrafigi extends StatefulWidget {
  final String solute;
  final double wtX;
  final double tempC;

  const InteraktifFazGrafigi({
    super.key,
    required this.solute,
    required this.wtX,
    required this.tempC,
  });

  @override
  State<InteraktifFazGrafigi> createState() => _InteraktifFazGrafigiState();
}

class _InteraktifFazGrafigiState extends State<InteraktifFazGrafigi> {
  List<_FazNoktasi> data = [];
  bool isLoading = true;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    fetchPhaseData();
  }

  Future<void> fetchPhaseData() async {
    final uri = Uri.parse('http://127.0.0.1:8000/phase-diagram-data');

    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'solute': widget.solute,
          'wt_x': widget.wtX,
          'T_C': widget.tempC,
        }),
      );

      if (response.statusCode == 200) {
        final jsonData = json.decode(response.body);
        final List<_FazNoktasi> parsedData = [];

        final x = jsonData['x'] as List<dynamic>;
        final y = jsonData['y'] as List<dynamic>;
        final phases = jsonData['phases'] as List<dynamic>;

        for (int i = 0; i < x.length; i++) {
          parsedData.add(_FazNoktasi(
            x: x[i].toDouble(),
            y: y[i].toDouble(),
            phase: phases[i],
          ));
        }

        setState(() {
          data = parsedData;
          isLoading = false;
        });
      } else {
        setState(() {
          errorMessage = 'Veri alınamadı: ${response.statusCode}';
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        errorMessage = 'Hata oluştu: ${e.toString()}';
        isLoading = false;
      });
    }
  }

  Color _getColor(String phase) {
    switch (phase) {
      case 'LIQUID':
        return Colors.red;
      case 'BCC_A2':
        return Colors.blue;
      case 'FCC_A1':
        return Colors.green;
      case 'CEMENTITE':
        return Colors.brown;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) return Center(child: CircularProgressIndicator());
    if (errorMessage != null) return Text(errorMessage!);

    return SfCartesianChart(
      title: ChartTitle(text: 'Interaktif Faz Diyagramı'),
      legend: Legend(isVisible: false),
      zoomPanBehavior: ZoomPanBehavior(
        enablePinching: true,
        enablePanning: true,
        zoomMode: ZoomMode.xy,
      ),
      tooltipBehavior: TooltipBehavior(enable: true),
      primaryXAxis: NumericAxis(
        title: AxisTitle(text: '${widget.solute} (wt%)'),
        edgeLabelPlacement: EdgeLabelPlacement.shift,
      ),
      primaryYAxis: NumericAxis(
        title: AxisTitle(text: 'Sıcaklık (°C)'),
      ),
      series: [
        ScatterSeries<_FazNoktasi, double>(
          dataSource: data,
          xValueMapper: (datum, _) => datum.x,
          yValueMapper: (datum, _) => datum.y,
          pointColorMapper: (datum, _) => _getColor(datum.phase),
          markerSettings: MarkerSettings(isVisible: true),
          name: 'Fazlar',
          enableTooltip: true,
        ),
      ],
    );
  }
}

class _FazNoktasi {
  final double x;
  final double y;
  final String phase;

  _FazNoktasi({required this.x, required this.y, required this.phase});
}
