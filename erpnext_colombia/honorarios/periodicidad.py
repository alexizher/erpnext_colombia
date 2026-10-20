"""Cuándo toca cobrar un honorario. Sin base de datos: solo fechas y meses."""

import datetime
from dataclasses import dataclass

MESES = (
	"enero", "febrero", "marzo", "abril", "mayo", "junio",
	"julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)  # fmt: skip
# Cada cuántos meses se cobra; "Una vez" no se repite.
MESES_ENTRE_COBROS = {
	"Mensual": 1,
	"Bimestral": 2,
	"Trimestral": 3,
	"Semestral": 6,
	"Anual": 12,
	"Una vez": None,
}


@dataclass(frozen=True, order=True)
class Periodo:
	"""Un mes de facturación."""

	anio: int
	mes: int

	@classmethod
	def de(cls, fecha: datetime.date) -> "Periodo":
		return cls(fecha.year, fecha.month)

	@property
	def indice(self) -> int:
		return self.anio * 12 + self.mes - 1

	@property
	def nombre(self) -> str:
		return f"{MESES[self.mes - 1]} de {self.anio}"

	def siguiente(self) -> "Periodo":
		return Periodo(self.anio + self.mes // 12, self.mes % 12 + 1)

	def __str__(self) -> str:
		return f"{self.anio}-{self.mes:02d}"


@dataclass(frozen=True)
class Honorario:
	concepto: str
	valor: float
	periodicidad: str
	desde: datetime.date
	hasta: datetime.date | None = None

	def toca_en(self, periodo: Periodo) -> bool:
		inicio = Periodo.de(self.desde)
		if periodo < inicio or (self.hasta and periodo > Periodo.de(self.hasta)):
			return False
		cada = MESES_ENTRE_COBROS[self.periodicidad]
		if cada is None:
			return periodo == inicio
		return (periodo.indice - inicio.indice) % cada == 0
