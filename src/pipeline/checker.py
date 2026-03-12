class MRZChecker:
    CONFUSIONS = {
        "O": "0",
        "0": "O",
        "I": "1",
        "1": "I",
        "Z": "2",
        "2": "Z",
        "S": "5",
        "5": "S",
        "B": "8",
        "8": "B",
    }

    @staticmethod
    def char_value(c: str) -> int:
        if c.isdigit():
            return int(c)
        if "A" <= c <= "Z":
            return ord(c) - 55
        return 0

    @classmethod
    def mrz_checksum(cls, field: str) -> int:
        weights = [7, 3, 1]
        return sum(cls.char_value(c) * weights[i % 3] for i, c in enumerate(field)) % 10

    @classmethod
    def validate_field(cls, field: str, check_digit: str) -> bool:
        if not check_digit.isdigit():
            return False
        return cls.mrz_checksum(field) == int(check_digit)

    @classmethod
    def try_fix_field(cls, field: str, check_digit: str) -> str:
        """Попытка исправить один field по check digit"""
        if cls.validate_field(field, check_digit):
            return field
        for i, c in enumerate(field):
            if c in cls.CONFUSIONS:
                candidate = field[:i] + cls.CONFUSIONS[c] + field[i + 1 :]
                if cls.validate_field(candidate, check_digit):
                    return candidate
        return field

    @classmethod
    def fix_mrz(cls, mrz_lines: list[str]) -> list[str]:
        """Исправление MRZ TD3 (2 строки по 44 символа)"""
        if len(mrz_lines) != 2:
            return mrz_lines

        line1, line2 = mrz_lines

        # разбор второй строки на поля
        passport_number = line2[0:9]
        passport_cd = line2[9]
        birth = line2[13:19]
        birth_cd = line2[19]
        expiry = line2[21:27]
        expiry_cd = line2[27]
        personal_number = line2[28:42]
        personal_cd = line2[42]

        # исправляем каждое поле
        passport_number = cls.try_fix_field(passport_number, passport_cd)
        birth = cls.try_fix_field(birth, birth_cd)
        expiry = cls.try_fix_field(expiry, expiry_cd)
        personal_number = cls.try_fix_field(personal_number, personal_cd)

        # собираем обратно
        fixed_line2 = (
            passport_number
            + passport_cd
            + line2[10:13]
            + birth
            + birth_cd
            + line2[20]
            + expiry
            + expiry_cd
            + personal_number
            + personal_cd
        )

        return [line1, fixed_line2]
