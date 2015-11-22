import java.util.*;

public class CurvingGrades
{

	public static int Curve(int max)
	{
		return 100 - max;

	}

	public static void main(String[] args)
	{
		Scanner console = new Scanner(System.in);

		System.out.print("How many grades will you enter? ");
		int amountOfGrades = console.nextInt();
		System.out.print("Enter grade 1: ");
		int currentInput = console.nextInt();

		int max = currentInput;

		int[] grades = new int[amountOfGrades];
		grades[0] = currentInput;
		for (int i = 1; i < amountOfGrades; i++)
		{
			// ask the user for input
			System.out.print("Enter grade " + (i + 1) + ": ");
			currentInput = console.nextInt();
			grades[i] = currentInput;

			if (currentInput > max)
			{
				max = currentInput;
			}

		}
		int c = Curve(max);
		for (int x = 0; x < grades.length; x++)
		{
			System.out.println("Original: " + grades[x] + " With Curve: " + (grades[x] + c));
		}

	}

}
